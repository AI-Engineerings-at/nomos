/**
 * NomOS Card — Container with light shadow, rounded corners, dark mode compatible.
 * Used for panels, agent badges, dashboard sections.
 */
'use client';

import { forwardRef, type HTMLAttributes } from 'react';

interface CardProps extends HTMLAttributes<HTMLDivElement> {
  /** Whether to show hover shadow elevation effect. */
  hoverable?: boolean;
  /** Optional padding override. Defaults to p-6. */
  padding?: 'none' | 'sm' | 'md' | 'lg';
}

const paddingStyles = {
  none: '',
  sm: 'p-3',
  md: 'p-6',
  lg: 'p-8',
};

export const Card = forwardRef<HTMLDivElement, CardProps>(function Card(
  { hoverable = false, padding = 'md', className = '', children, ...props },
  ref,
) {
  return (
    <div
      ref={ref}
      className={[
        'bg-[var(--color-card)] border border-[var(--color-border)]',
        'rounded-[var(--radius)] shadow-[var(--shadow-card)]',
        'transition-shadow duration-[var(--transition)]',
        hoverable ? 'hover:shadow-[var(--shadow-card-hover)] cursor-pointer' : '',
        paddingStyles[padding],
        className,
      ].join(' ')}
      {...props}
    >
      {children}
    </div>
  );
});

interface CardHeaderProps extends HTMLAttributes<HTMLDivElement> {
  /** Section title rendered as h3 with Montserrat font. */
  title: string;
  /** Optional description text below the title. */
  description?: string;
  /** Optional action element (button, link) displayed on the right. */
  action?: React.ReactNode;
}

export function CardHeader({ title, description, action, className = '', ...props }: CardHeaderProps) {
  return (
    <div className={`flex items-start justify-between gap-4 ${className}`} {...props}>
      <div>
        <h3 className="text-lg font-bold text-[var(--color-text)]">{title}</h3>
        {description && (
          <p className="mt-1 text-sm text-[var(--color-muted)]">{description}</p>
        )}
      </div>
      {action && <div className="shrink-0">{action}</div>}
    </div>
  );
}
