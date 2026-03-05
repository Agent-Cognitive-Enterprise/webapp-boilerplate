import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import ConfirmDeleteModal from './ConfirmDelete';

vi.mock('../UiLabel.tsx', () => ({
  default: ({ k }: { k: string }) => <span>{k}</span>,
}));

vi.mock('../../hooks/useT.ts', () => ({
  useT: (key: string) => key,
}));

describe('ConfirmDeleteModal', () => {
  it('does not render when closed', () => {
    const { container } = render(
      <ConfirmDeleteModal isOpen={false} onClose={vi.fn()} onConfirm={vi.fn()} />
    );
    expect(container).toBeEmptyDOMElement();
  });

  it('enables delete only when code matches and confirms action', () => {
    const onClose = vi.fn();
    const onConfirm = vi.fn();

    render(
      <ConfirmDeleteModal
        isOpen
        onClose={onClose}
        onConfirm={onConfirm}
        title="Delete Chapter"
      />
    );

    const code = screen.getAllByText(/^\d{4}$/)[0].textContent ?? '';
    const input = screen.getByPlaceholderText('confirm_delete_modal.placeholder.enter_code_here');
    const deleteButton = screen.getByRole('button', { name: 'button.delete' });

    expect(deleteButton).toBeDisabled();
    fireEvent.change(input, { target: { value: code } });
    expect(deleteButton).not.toBeDisabled();

    fireEvent.click(deleteButton);
    expect(onConfirm).toHaveBeenCalledTimes(1);
    expect(onClose).toHaveBeenCalledTimes(1);
  });
});

