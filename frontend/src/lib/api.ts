const API_URL = process.env.NEXT_PUBLIC_API_URL || '';

export async function searchQuery(query: string) {
  const response = await fetch(`${API_URL}/api/search`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ query }),
  });
  
  if (!response.ok) {
    throw new Error('Search failed');
  }
  
  return response.json();
}

export async function getResults(jobId: string) {
  const response = await fetch(`${API_URL}/api/results/${jobId}`);
  
  if (!response.ok) {
    throw new Error('Failed to fetch results');
  }
  
  return response.json();
}

export async function getLogs(jobId: string) {
  const response = await fetch(`${API_URL}/api/results/${jobId}/logs`);
  
  if (!response.ok) {
    throw new Error(`Failed to fetch logs: ${response.status}`);
  }
  
  return response.json();
}

