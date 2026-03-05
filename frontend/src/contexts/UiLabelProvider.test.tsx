import {describe, it, expect, vi, beforeEach, afterEach} from 'vitest';
import {act, render, screen} from '@testing-library/react';
import React from 'react';

import {UiLabelProvider} from './UiLabelProvider';
import {AuthContext} from './AuthContext';
import {useUiLabel} from '../hooks/useUiLabel';
import api from '../api/api';

vi.mock('../api/api', () => ({
  default: {
    post: vi.fn(),
  },
}));

function Probe() {
  const {value: frValue} = useUiLabel('greeting.hello', 'fr');
  const {value: enValue} = useUiLabel('greeting.hello', 'en');
  return <div data-testid="value">{frValue ?? enValue ?? ''}</div>;
}

const authContextValue = {
  token: null,
  user: null,
  login: vi.fn(),
  register: vi.fn(),
  logout: vi.fn(),
  setToken: vi.fn(),
};

describe('UiLabelProvider fallback flow', () => {
  beforeEach(() => {
    vi.useFakeTimers();
    vi.clearAllMocks();
    localStorage.clear();

    localStorage.setItem(
      'ui_label_cache_v1',
      JSON.stringify({
        en: {
          values: {'greeting.hello': 'Hello'},
          values_hash: 'hash-en',
          last_check: Date.now(),
        },
      }),
    );
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it('shows english fallback without storing it in locale cache, then replaces with locale translation', async () => {
    let frGetCalls = 0;

    vi.mocked(api.post).mockImplementation(async (url: string, payload: any) => {
      expect(url).toBe('/ui-label');

      if (payload.action === 'add') {
        return {data: {success: true, message: 'scheduled for translation'}} as any;
      }

      if (payload.action === 'get' && payload.locale === 'fr') {
        frGetCalls += 1;
        if (frGetCalls < 2) {
          return {
            data: {
              success: true,
              data: {locale: 'fr', values_hash: 'hash-fr-1', labels: {}},
            },
          } as any;
        }

        return {
          data: {
            success: true,
            data: {
              locale: 'fr',
              values_hash: 'hash-fr-2',
              labels: {'greeting.hello': 'Bonjour'},
            },
          },
        } as any;
      }

      return {
        data: {
          success: true,
          data: {values_hash: 'noop'},
        },
      } as any;
    });

    render(
      <AuthContext.Provider value={authContextValue as any}>
        <UiLabelProvider>
          <Probe />
        </UiLabelProvider>
      </AuthContext.Provider>,
    );

    await act(async () => {
      await vi.advanceTimersByTimeAsync(1);
    });
    expect(screen.getByTestId('value').textContent).toBe('Hello');
    const cacheAfterFirstTick = JSON.parse(localStorage.getItem('ui_label_cache_v1') ?? '{}');
    expect(cacheAfterFirstTick.fr?.values?.['greeting.hello']).toBeUndefined();

    await act(async () => {
      await vi.advanceTimersByTimeAsync(120_000);
    });
    expect(screen.getByTestId('value').textContent).toBe('Bonjour');
  });
});
