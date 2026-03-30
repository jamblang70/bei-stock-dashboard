import { render, screen, fireEvent, act } from '@testing-library/react'
import { vi, describe, it, expect, beforeEach } from 'vitest'

// ── Mocks ──────────────────────────────────────────────────────────────────────

const mockPush = vi.fn()

vi.mock('next/navigation', () => ({
  useRouter: () => ({ push: mockPush }),
}))

const mockUseSession = vi.fn()
vi.mock('next-auth/react', () => ({
  useSession: () => mockUseSession(),
}))

const mockApiGet = vi.fn()
const mockApiPost = vi.fn()
vi.mock('@/lib/api', () => ({
  apiGet: (...args: any[]) => mockApiGet(...args),
  apiPost: (...args: any[]) => mockApiPost(...args),
}))

// ── Lazy imports after mocks ───────────────────────────────────────────────────

import SearchBar from '@/components/search/SearchBar'
import ScoreCard from '@/components/stock/ScoreCard'
import AddToWatchlistButton from '@/components/watchlist/AddToWatchlistButton'
import type { ScoreInfo } from '@/types'

// ── SearchBar Tests ────────────────────────────────────────────────────────────

describe('SearchBar', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    vi.useFakeTimers({ shouldAdvanceTime: true })
  })

  afterEach(() => {
    vi.runAllTimers()
    vi.useRealTimers()
  })

  it('shows "Saham tidak ditemukan" when no results', async () => {
    mockApiGet.mockResolvedValue([])
    render(<SearchBar />)

    fireEvent.change(screen.getByRole('searchbox'), {
      target: { value: 'XXXX' },
    })

    // API should NOT be called yet (before debounce delay)
    expect(mockApiGet).not.toHaveBeenCalled()

    // Advance past the 300ms debounce and flush promises
    await act(async () => {
      vi.advanceTimersByTime(350)
      await Promise.resolve()
    })

    expect(screen.getByText('Saham tidak ditemukan')).toBeInTheDocument()
  })

  it('shows dropdown with results', async () => {
    mockApiGet.mockResolvedValue([
      { id: 1, code: 'BBCA', name: 'Bank Central Asia', sector: 'Keuangan', sub_sector: null, is_active: true },
    ])
    render(<SearchBar />)

    fireEvent.change(screen.getByRole('searchbox'), {
      target: { value: 'BBCA' },
    })

    await act(async () => {
      vi.advanceTimersByTime(350)
      await Promise.resolve()
    })

    expect(screen.getByRole('listbox')).toBeInTheDocument()
    expect(screen.getByText('BBCA')).toBeInTheDocument()
  })

  it('debounces input — API not called immediately on typing', async () => {
    mockApiGet.mockResolvedValue([])
    render(<SearchBar />)

    fireEvent.change(screen.getByRole('searchbox'), {
      target: { value: 'B' },
    })

    // API should NOT be called yet (before debounce delay)
    expect(mockApiGet).not.toHaveBeenCalled()

    // Advance past debounce and flush
    await act(async () => {
      vi.advanceTimersByTime(350)
      await Promise.resolve()
    })

    expect(mockApiGet).toHaveBeenCalledTimes(1)
  })
})

// ── ScoreCard Tests ────────────────────────────────────────────────────────────

function makeScore(score: number): ScoreInfo {
  return {
    score,
    valuation_score: 70,
    quality_score: 70,
    momentum_score: 70,
    recommendation: 'Tahan',
    is_partial: false,
    score_factors: [],
    calculated_at: '2024-01-01T00:00:00Z',
  }
}

describe('ScoreCard', () => {
  it('shows "Sangat Baik" for score >= 80', () => {
    render(<ScoreCard score={makeScore(85)} />)
    expect(screen.getByText('Sangat Baik')).toBeInTheDocument()
  })

  it('shows "Baik" for score 60-79', () => {
    render(<ScoreCard score={makeScore(65)} />)
    expect(screen.getByText('Baik')).toBeInTheDocument()
  })

  it('shows "Cukup" for score 40-59', () => {
    render(<ScoreCard score={makeScore(50)} />)
    expect(screen.getByText('Cukup')).toBeInTheDocument()
  })

  it('shows "Perlu Perhatian" for score < 40', () => {
    render(<ScoreCard score={makeScore(30)} />)
    expect(screen.getByText('Perlu Perhatian')).toBeInTheDocument()
  })
})

// ── AddToWatchlistButton Tests ─────────────────────────────────────────────────

describe('AddToWatchlistButton', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('shows login button when not authenticated', () => {
    mockUseSession.mockReturnValue({ data: null, status: 'unauthenticated' })
    render(<AddToWatchlistButton stockCode="BBCA" />)
    expect(screen.getByRole('button', { name: /login untuk watchlist/i })).toBeInTheDocument()
  })

  it('redirects to login when clicked and not authenticated', () => {
    mockUseSession.mockReturnValue({ data: null, status: 'unauthenticated' })
    render(<AddToWatchlistButton stockCode="BBCA" />)

    fireEvent.click(screen.getByRole('button', { name: /login untuk watchlist/i }))
    expect(mockPush).toHaveBeenCalledWith('/login')
  })
})
