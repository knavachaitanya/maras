import { create } from 'zustand'

interface SearchState {
  currentQuery: string
  jobId: string | null
  results: any[]
  status: 'idle' | 'loading' | 'complete' | 'error'
  setQuery: (query: string) => void
  setJobId: (id: string) => void
  setResults: (results: any[]) => void
  setStatus: (status: SearchState['status']) => void
  reset: () => void
}

export const useSearchStore = create<SearchState>((set) => ({
  currentQuery: '',
  jobId: null,
  results: [],
  status: 'idle',
  setQuery: (query) => set({ currentQuery: query }),
  setJobId: (id) => set({ jobId: id }),
  setResults: (results) => set({ results }),
  setStatus: (status) => set({ status }),
  reset: () => set({ currentQuery: '', jobId: null, results: [], status: 'idle' }),
}))
