import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { vi, describe, it, expect, beforeEach } from 'vitest'

// ── Mocks ──────────────────────────────────────────────────────────────────────

const mockPush = vi.fn()

vi.mock('next/navigation', () => ({
  useRouter: () => ({ push: mockPush }),
  useSearchParams: () => ({ get: () => null }),
}))

const mockSignIn = vi.fn()
vi.mock('next-auth/react', () => ({
  signIn: (...args: any[]) => mockSignIn(...args),
}))

const mockApiPost = vi.fn()
vi.mock('@/lib/api', () => ({
  apiPost: (...args: any[]) => mockApiPost(...args),
}))

// ── Lazy imports after mocks ───────────────────────────────────────────────────

import LoginPage from '@/app/(auth)/login/page'
import RegisterPage from '@/app/(auth)/register/page'

// ── Login Tests ────────────────────────────────────────────────────────────────

describe('LoginPage', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders login form with email and password fields', () => {
    render(<LoginPage />)
    expect(screen.getByLabelText(/email/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/password/i)).toBeInTheDocument()
  })

  it('shows error message on failed login', async () => {
    mockSignIn.mockResolvedValue({ error: 'CredentialsSignin' })
    render(<LoginPage />)

    fireEvent.change(screen.getByLabelText(/email/i), {
      target: { value: 'test@example.com' },
    })
    fireEvent.change(screen.getByLabelText(/password/i), {
      target: { value: 'wrongpassword' },
    })
    fireEvent.click(screen.getByRole('button', { name: /masuk/i }))

    await waitFor(() => {
      expect(screen.getByText(/email atau password tidak valid/i)).toBeInTheDocument()
    })
  })

  it('does not reveal specific field in error message', async () => {
    mockSignIn.mockResolvedValue({ error: 'CredentialsSignin' })
    render(<LoginPage />)

    fireEvent.change(screen.getByLabelText(/email/i), {
      target: { value: 'test@example.com' },
    })
    fireEvent.change(screen.getByLabelText(/password/i), {
      target: { value: 'wrongpassword' },
    })
    fireEvent.click(screen.getByRole('button', { name: /masuk/i }))

    await waitFor(() => {
      const errorEl = screen.getByText(/email atau password tidak valid/i)
      // Error message must not single out email or password alone
      expect(errorEl.textContent).not.toMatch(/^email tidak/i)
      expect(errorEl.textContent).not.toMatch(/^password tidak/i)
    })
  })

  it('redirects to dashboard on successful login', async () => {
    mockSignIn.mockResolvedValue({ error: null })
    render(<LoginPage />)

    fireEvent.change(screen.getByLabelText(/email/i), {
      target: { value: 'test@example.com' },
    })
    fireEvent.change(screen.getByLabelText(/password/i), {
      target: { value: 'correctpassword' },
    })
    fireEvent.click(screen.getByRole('button', { name: /masuk/i }))

    await waitFor(() => {
      expect(mockPush).toHaveBeenCalledWith('/dashboard')
    })
  })
})

// ── Register Tests ─────────────────────────────────────────────────────────────

describe('RegisterPage', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders register form with name, email, password fields', () => {
    render(<RegisterPage />)
    expect(screen.getByLabelText(/nama lengkap/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/email/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/password/i)).toBeInTheDocument()
  })

  it('shows API error message on failed registration', async () => {
    const apiError = {
      response: { data: { detail: 'Email sudah terdaftar' } },
    }
    mockApiPost.mockRejectedValue(apiError)
    render(<RegisterPage />)

    fireEvent.change(screen.getByLabelText(/nama lengkap/i), {
      target: { value: 'Test User' },
    })
    fireEvent.change(screen.getByLabelText(/email/i), {
      target: { value: 'existing@example.com' },
    })
    fireEvent.change(screen.getByLabelText(/password/i), {
      target: { value: 'password123' },
    })
    fireEvent.click(screen.getByRole('button', { name: /daftar/i }))

    await waitFor(() => {
      expect(screen.getByText('Email sudah terdaftar')).toBeInTheDocument()
    })
  })

  it('redirects to login on successful registration', async () => {
    mockApiPost.mockResolvedValue({})
    render(<RegisterPage />)

    fireEvent.change(screen.getByLabelText(/nama lengkap/i), {
      target: { value: 'Test User' },
    })
    fireEvent.change(screen.getByLabelText(/email/i), {
      target: { value: 'new@example.com' },
    })
    fireEvent.change(screen.getByLabelText(/password/i), {
      target: { value: 'password123' },
    })
    fireEvent.click(screen.getByRole('button', { name: /daftar/i }))

    await waitFor(() => {
      expect(mockPush).toHaveBeenCalledWith('/login?registered=1')
    })
  })
})
