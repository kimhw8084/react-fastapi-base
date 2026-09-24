import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import { WorkspaceShell } from './WorkspaceShell'

describe('WorkspaceShell density', () => {
  it('keeps Knowledge task actions and summary available in the compact shell', () => {
    render(
      <WorkspaceShell
        title="Engineering knowledge"
        density="compact"
        actions={<button type="button">Refresh</button>}
        metrics={[{ label: 'Published', value: 1 }]}
      >
        <article>Runbook material</article>
      </WorkspaceShell>,
    )

    const taskStart = screen.getByTestId('workspace-task-start')
    expect(taskStart.parentElement).toHaveClass('workspace', 'workspace--compact')
    expect(screen.getByRole('heading', { name: 'Engineering knowledge' })).toBeVisible()
    expect(screen.getByRole('button', { name: 'Refresh' })).toBeVisible()
    expect(screen.getByRole('region', { name: 'Workspace summary' })).toHaveTextContent('Published')
    expect(screen.getByText('Runbook material')).toBeVisible()
  })
})
