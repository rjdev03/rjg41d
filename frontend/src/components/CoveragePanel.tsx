
import type { Coverage } from '../types'

interface CoveragePanelProps {
  coverage: Coverage
}

interface CoverageItemProps {
  label: string
  available: number
  expected: number
  description: string
}

function CoverageItem({
  label,
  available,
  expected,
  description,
}: CoverageItemProps) {
  const percentage =
    expected > 0 ? (available / expected) * 100 : 0

  return (
    <div>
      <div className="flex items-center justify-between gap-4">
        <p className="text-sm font-medium text-slate-700">
          {label}
        </p>

        <p className="text-sm font-semibold tabular-nums text-slate-900">
          {available}/{expected}
        </p>
      </div>

      <div
        className="mt-2 h-2 overflow-hidden rounded-full bg-slate-100"
        role="progressbar"
        aria-label={label}
        aria-valuenow={available}
        aria-valuemin={0}
        aria-valuemax={expected}
      >
        <div
          className="h-full rounded-full bg-blue-600 transition-all"
          style={{ width: `${percentage}%` }}
        />
      </div>

      <p className="mt-1.5 text-xs text-slate-500">
        {description}
      </p>
    </div>
  )
}

function CoveragePanel({ coverage }: CoveragePanelProps) {
  const items: CoverageItemProps[] = [
    {
      label: 'Forecast availability',
      available: coverage.forecast_hours_available,
      expected: coverage.expected_hours,
      description: `${coverage.missing_forecast_hours} forecast hours missing`,
    },
    {
      label: 'Actual availability',
      available: coverage.actual_hours_available,
      expected: coverage.expected_hours,
      description: `${coverage.missing_actual_hours} actual hours missing`,
    },
    {
      label: 'Successfully evaluated',
      available: coverage.evaluated_hours,
      expected: coverage.expected_hours,
      description: `${coverage.expected_hours - coverage.evaluated_hours} hours not evaluated`,
    },
  ]

  return (
    <section
      aria-labelledby="coverage-heading"
      className="mt-6 rounded-xl border border-slate-200 bg-white p-5 shadow-sm"
    >
      <div className="mb-5">
        <h2
          id="coverage-heading"
          className="text-lg font-semibold text-slate-900"
        >
          Data availability and evaluation
        </h2>

        <p className="mt-1 text-sm text-slate-500">
          Availability of forecast and actual observations across
          the delivery day.
        </p>
      </div>

      <div className="grid gap-5 md:grid-cols-3">
        {items.map((item) => (
          <CoverageItem key={item.label} {...item} />
        ))}
      </div>
    </section>
  )
}

export default CoveragePanel
