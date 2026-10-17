import { render, screen, within } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import App from './App'

describe('App', () => {
  it('renders the application title and three navigation placeholders', () => {
    render(<App />)

    expect(screen.getByRole('heading', { level: 1, name: '공채 모아보기' })).toBeVisible()

    const navigation = screen.getByRole('navigation', { name: '주요 메뉴' })
    expect(within(navigation).getAllByRole('listitem')).toHaveLength(3)
    for (const label of ['결과', '조건 승인', '실행 기록']) {
      expect(within(navigation).getByText(label, { exact: true })).toBeVisible()
    }
    expect(screen.getByRole('main')).toBeInTheDocument()
  })
})
