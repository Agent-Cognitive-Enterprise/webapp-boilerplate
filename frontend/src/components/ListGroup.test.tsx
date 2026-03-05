import { describe, it, expect } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import ListGroup from './ListGroup';

describe('ListGroup Component', () => {
  it('renders default heading and list items', () => {
    render(<ListGroup items={['A', 'B']} />);
    expect(screen.getByRole('heading', { name: 'List' })).toBeInTheDocument();
    expect(screen.getByText('A')).toBeInTheDocument();
    expect(screen.getByText('B')).toBeInTheDocument();
  });

  it('supports custom heading and item selection state', () => {
    render(<ListGroup items={['One', 'Two']} heading="Custom" />);
    expect(screen.getByRole('heading', { name: 'Custom' })).toBeInTheDocument();

    const twoItem = screen.getByText('Two');
    fireEvent.click(twoItem);

    expect(twoItem.className).toContain('bg-blue-500');
  });
});

