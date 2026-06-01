const axios = require('axios');

class QueryUnderstanding {
  constructor(openaiApiKey) {
    this.apiKey = openaiApiKey;
  }

  async analyze(query) {
    const stopwords = ['a','an','the','is','are','was','were','be','been','being','have','has','had','do','does','did','will','would','could','should','may','might','shall','can','need','dare','ought','used','to','of','in','for','on','with','at','by','from','up','about','into','through','during','before','after','above','below','between','out','off','over','under','again','further','then','once','and','but','or','nor','so','yet','both','either','neither','not','only','own','same','than','too','very','just','i','me','my','myself','we','our','ours','ourselves','you','your','yours','yourself','he','him','his','himself','she','her','hers','herself','it','its','itself','they','them','their','theirs','themselves','what','which','who','whom','this','that','these','those','best','top','good','how'];

    const tokens = query.toLowerCase()
      .replace(/[^\w\s]/g, '')
      .split(/\s+/)
      .filter(w => w.length > 1 && !stopwords.includes(w));

    let intent = { topic: query, keywords: tokens, category: 'general', priceContext: null, locationContext: null };

    if (this.apiKey) {
      try {
        const response = await axios.post('https://api.openai.com/v1/chat/completions', {
          model: 'gpt-3.5-turbo',
          max_tokens: 200,
          messages: [
            {
              role: 'system',
              content: 'You are a universal search intent analyzer. Given any user query in any language or topic, extract the search intent. Return only valid JSON with: topic (2-4 word summary of what they want), keywords (array of 6-8 specific meaningful words from this exact query that relevant results must contain), category (product/finance/technology/health/travel/food/education/news/general), priceContext (price range mentioned or null), locationContext (location mentioned or null), searchQueries (array of 4 specific search engine queries that will find exactly what this user wants, each query must be about this specific topic only). Be completely specific to the input query. Never reuse keywords from previous queries.'
            },
            { role: 'user', content: `Query: "${query}"` }
          ]
        }, {
          headers: { 'Authorization': `Bearer ${this.apiKey}`, 'Content-Type': 'application/json' }
        });
        const text = response.data.choices[0].message.content.trim();
        const parsed = JSON.parse(text.replace(/```json|```/g, '').trim());
        intent = { ...intent, ...parsed };
        intent.keywords = this.normalizeKeywords(intent.keywords || tokens);
        console.log('[QueryUnderstanding] AI intent:', JSON.stringify(intent));
      } catch (err) {
        console.log('[QueryUnderstanding] AI failed, using token fallback:', err.message);
        intent = this.fallbackIntent(query, tokens);
      }
    } else {
      intent = this.fallbackIntent(query, tokens);
    }

    return intent;
  }

  scoreResult(intent, result) {
    const title = (result.title || '').toLowerCase();
    const description = (result.description || '').toLowerCase();
    const url = (result.url || '').toLowerCase();
    const combined = title + ' ' + description + ' ' + url;

    let score = 0;
    const keywordMatches = (intent.keywords || []).filter(kw => combined.includes(kw.toLowerCase()));
    const keywordRatio = keywordMatches.length / Math.max((intent.keywords || []).length, 1);

    if (keywordMatches.length < 2 && (intent.keywords || []).length > 3) {
      return 5;
    }

    score += keywordRatio * 50;

    const titleMatches = (intent.keywords || []).filter(kw => title.includes(kw.toLowerCase()));
    score += (titleMatches.length / Math.max((intent.keywords || []).length, 1)) * 25;

    if (intent.priceContext && combined.includes(intent.priceContext.replace(/[^\d]/g, '').slice(0, 4))) {
      score += 10;
    }

    if (intent.locationContext && combined.includes(intent.locationContext.toLowerCase())) {
      score += 10;
    }

    const topicWords = (intent.topic || '').toLowerCase().split(' ');
    const topicMatches = topicWords.filter(w => w.length > 3 && combined.includes(w));
    score += (topicMatches.length / Math.max(topicWords.length, 1)) * 5;

    return Math.min(Math.round(score), 100);
  }

  filterIrrelevant(intent, results) {
    return results
      .map(r => ({ ...r, relevance_score: this.scoreResult(intent, r) }))
      .filter(r => r.relevance_score >= 20)
      .sort((a, b) => b.relevance_score - a.relevance_score);
  }

  normalizeKeywords(tokens) {
    const generic = new Set(['best', 'top', 'good', 'review', 'reviews', 'under', 'below', 'above', 'near', 'latest']);
    const keywords = [];
    for (const token of tokens) {
      const value = String(token || '').toLowerCase().trim();
      if (value.length > 2 && !generic.has(value) && !keywords.includes(value)) {
        keywords.push(value);
      }
    }
    return keywords.slice(0, 8);
  }

  fallbackIntent(query, tokens) {
    const keywords = this.normalizeKeywords([...this.extractKeyphrases(query), ...tokens]);
    const topicWords = tokens.filter(token => token.length > 2).slice(0, 4);
    const topic = topicWords.join(' ') || keywords.slice(0, 4).join(' ') || query;
    const priceMatch = query.match(/(?:under|below|less than|upto|up to|over|above)?\s*(?:₹|rs\.?|inr|\$|€|£)?\s*\d[\d,]*(?:\.\d+)?\s*(?:k|m|lakh|lakhs|crore|crores)?/i);
    const locationMatch = query.match(/\b(?:in|near|around|at)\s+([a-z][a-z\s]{2,30}?)(?:\s+(?:for|with|under|below|above|near|at)\b|$)/i);
    const simpleKeywords = keywords.filter(keyword => !keyword.includes(' '));
    const intent = {
      topic,
      keywords,
      category: this.inferCategory(query, keywords),
      priceContext: priceMatch ? priceMatch[0].trim() : null,
      locationContext: locationMatch ? locationMatch[1].trim() : null,
      searchQueries: [
        query,
        simpleKeywords.slice(0, 6).join(' ') || keywords.slice(0, 4).join(' ') || query,
        `${topic} ${priceMatch ? priceMatch[0].trim() : ''}`.trim(),
        `${topic} ${locationMatch ? locationMatch[1].trim() : ''}`.trim()
      ]
    };
    intent.searchQueries = this.ensureFourQueries(intent.searchQueries, topic);
    return intent;
  }

  ensureFourQueries(queries, topic) {
    const output = [...new Set(queries.filter(Boolean).map(q => q.trim()).filter(Boolean))];
    for (const suffix of ['guide', 'latest', 'reviews', 'explained']) {
      if (output.length >= 4) break;
      output.push(`${topic} ${suffix}`.trim());
    }
    return output.slice(0, 4);
  }

  inferCategory(query, keywords) {
    const lower = query.toLowerCase();
    if (/\b(price|buy|cost|cheap|budget|under|below|deal)\b/.test(lower)) return 'product';
    if (/\b(symptom|doctor|deficiency|disease|medicine|treatment|health)\b/.test(lower)) return 'health';
    if (/\b(learn|tutorial|course|beginner|study|exam)\b/.test(lower)) return 'education';
    if (/\b(restaurant|dinner|lunch|food|cafe)\b/.test(lower)) return 'food';
    if (/\b(news|latest|today|breaking)\b/.test(lower)) return 'news';
    if (/\b(invest|fund|stock|tax|loan|finance)\b/.test(lower)) return 'finance';
    if (/\b(code|programming|software|computer|phone|laptop|ai)\b/.test(lower)) return 'technology';
    if (/\b(hotel|flight|travel|trip|tour)\b/.test(lower)) return 'travel';
    return keywords.length ? 'general' : 'general';
  }

  extractKeyphrases(query) {
    const stopwords = new Set(['a','an','the','is','are','was','were','be','been','being','have','has','had','do','does','did','will','would','could','should','may','might','shall','can','need','dare','ought','used','to','of','in','for','on','with','at','by','from','up','about','into','through','during','before','after','above','below','between','out','off','over','under','again','further','then','once','and','but','or','nor','so','yet','both','either','neither','not','only','own','same','than','too','very','just','i','me','my','myself','we','our','ours','ourselves','you','your','yours','yourself','he','him','his','himself','she','her','hers','herself','it','its','itself','they','them','their','theirs','themselves','what','which','who','whom','this','that','these','those','best','top','good','how']);
    const words = query.toLowerCase().replace(/[^\w\s]/g, ' ').split(/\s+/).filter(w => w && !stopwords.has(w));
    const phrases = [];
    for (let i = 0; i < words.length - 1; i += 1) {
      if (words[i].length > 2 || words[i + 1].length > 2) {
        const phrase = `${words[i]} ${words[i + 1]}`;
        if (!phrases.includes(phrase)) phrases.push(phrase);
      }
    }
    return phrases.slice(0, 4);
  }
}

module.exports = QueryUnderstanding;
