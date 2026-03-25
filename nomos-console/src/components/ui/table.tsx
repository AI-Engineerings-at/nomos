/**
 * NomOS Table — Sortable, responsive table component.
 * WCAG 2.2 AA: proper table semantics, aria-sort, keyboard accessible sort.
 */
'use client';

import { useState, useCallback, type ReactNode } from 'react';

export interface TableColumn<T> {
  /** Unique key for the column, must be a key of T or a string identifier. */
  key: string;
  /** Column header text. */
  header: string;
  /** Whether this column is sortable. */
  sortable?: boolean;
  /** Custom render function for cell content. */
  render?: (row: T, rowIndex: number) => ReactNode;
  /** CSS class for the column header and cells. */
  className?: string;
}

interface TableProps<T> {
  /** Column definitions. */
  columns: TableColumn<T>[];
  /** Row data. */
  data: T[];
  /** Function to extract a unique key from each row. */
  rowKey: (row: T, index: number) => string;
  /** Caption for accessibility (visually hidden but read by screen readers). */
  caption?: string;
  /** Text shown when data is empty. */
  emptyText?: string;
  /** Optional className for the table wrapper. */
  className?: string;
}

type SortDirection = 'asc' | 'desc';

interface SortState {
  key: string;
  direction: SortDirection;
}

export function Table<T extends Record<string, unknown>>({
  columns,
  data,
  rowKey,
  caption,
  emptyText = 'Keine Ergebnisse gefunden.',
  className = '',
}: TableProps<T>) {
  const [sort, setSort] = useState<SortState | null>(null);

  const handleSort = useCallback((key: string) => {
    setSort((prev) => {
      if (prev?.key === key) {
        return { key, direction: prev.direction === 'asc' ? 'desc' : 'asc' };
      }
      return { key, direction: 'asc' };
    });
  }, []);

  const handleSortKeyDown = useCallback(
    (key: string) => (e: React.KeyboardEvent) => {
      if (e.key === 'Enter' || e.key === ' ') {
        e.preventDefault();
        handleSort(key);
      }
    },
    [handleSort],
  );

  // Sort data if a sort column is selected
  const sortedData = sort
    ? [...data].sort((a, b) => {
        const aVal = a[sort.key];
        const bVal = b[sort.key];
        if (aVal == null && bVal == null) return 0;
        if (aVal == null) return sort.direction === 'asc' ? -1 : 1;
        if (bVal == null) return sort.direction === 'asc' ? 1 : -1;
        if (typeof aVal === 'string' && typeof bVal === 'string') {
          return sort.direction === 'asc'
            ? aVal.localeCompare(bVal)
            : bVal.localeCompare(aVal);
        }
        if (typeof aVal === 'number' && typeof bVal === 'number') {
          return sort.direction === 'asc' ? aVal - bVal : bVal - aVal;
        }
        return 0;
      })
    : data;

  return (
    <div className={`overflow-x-auto rounded-[var(--radius)] border border-[var(--color-border)] ${className}`}>
      <table className="w-full text-sm text-left">
        {caption && <caption className="sr-only">{caption}</caption>}
        <thead>
          <tr className="bg-[var(--color-hover)] border-b border-[var(--color-border)]">
            {columns.map((col) => (
              <th
                key={col.key}
                scope="col"
                className={[
                  'px-4 py-3 text-xs font-bold uppercase tracking-wider',
                  'text-[var(--color-muted)] font-[family-name:var(--font-headline)]',
                  col.sortable ? 'cursor-pointer select-none hover:text-[var(--color-text)]' : '',
                  col.className ?? '',
                ].join(' ')}
                aria-sort={
                  sort?.key === col.key
                    ? sort.direction === 'asc'
                      ? 'ascending'
                      : 'descending'
                    : col.sortable
                      ? 'none'
                      : undefined
                }
                onClick={col.sortable ? () => handleSort(col.key) : undefined}
                onKeyDown={col.sortable ? handleSortKeyDown(col.key) : undefined}
                tabIndex={col.sortable ? 0 : undefined}
                role={col.sortable ? 'columnheader button' : 'columnheader'}
              >
                <span className="inline-flex items-center gap-1.5">
                  {col.header}
                  {col.sortable && sort?.key === col.key && (
                    <svg
                      className="w-3.5 h-3.5"
                      viewBox="0 0 14 14"
                      fill="currentColor"
                      aria-hidden="true"
                    >
                      {sort.direction === 'asc' ? (
                        <path d="M7 3l4 5H3z" />
                      ) : (
                        <path d="M7 11l4-5H3z" />
                      )}
                    </svg>
                  )}
                </span>
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {sortedData.length === 0 ? (
            <tr>
              <td
                colSpan={columns.length}
                className="px-4 py-8 text-center text-[var(--color-muted)]"
              >
                {emptyText}
              </td>
            </tr>
          ) : (
            sortedData.map((row, rowIndex) => (
              <tr
                key={rowKey(row, rowIndex)}
                className="border-b border-[var(--color-border)] hover:bg-[var(--color-hover)] transition-colors duration-[var(--transition)]"
              >
                {columns.map((col) => (
                  <td
                    key={col.key}
                    className={`px-4 py-3 text-[var(--color-text)] ${col.className ?? ''}`}
                  >
                    {col.render
                      ? col.render(row, rowIndex)
                      : (String(row[col.key] ?? ''))}
                  </td>
                ))}
              </tr>
            ))
          )}
        </tbody>
      </table>
    </div>
  );
}
