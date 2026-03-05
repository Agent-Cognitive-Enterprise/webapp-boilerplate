import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import Alert from './Alert';
import { vi } from 'vitest';

vi.mock('./UiLabel.tsx', () => ({
  default: ({ k }: { k: string }) => <span>{k}</span>,
}));

describe('Alert Component', () => {
  it('renders alert content', () => {
    render(<Alert />);
    expect(screen.getByText('common.alert')).toBeInTheDocument();
  });
});
