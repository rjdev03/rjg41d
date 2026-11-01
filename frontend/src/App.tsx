
import { useEffect, useState } from 'react'
import type {
  AvailabilityResponse,
  WindAnalyticsResponse,
} from './types'
import MetricCard from './components/MetricCard'
import DashboardHeader from './components/DashboardHeader'
import HourlyGenerationTable from './components/HourlyGenerationTable'
import GenerationChart from './components/GenerationChart'
import CoveragePanel from './components/CoveragePanel'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL

if (!API_BASE_URL) {
  throw new Error('VITE_API_BASE_URL is not configured')
}

const numberFormatter = new Intl.NumberFormat('en-GB', {
  maximumFractionDigits: 1,
})

function formatMw(value: number | null): string {
  return value === null ? 'N/A' : `${numberFormatter.format(value)} MW`
}

function App() {
  const [availability, setAvailability] =
    useState<AvailabilityResponse | null>(null)
  const [selectedDate, setSelectedDate] = useState('')
  const [data, setData] = useState<WindAnalyticsResponse | null>(null)
  const [availabilityLoading, setAvailabilityLoading] = useState(true)
  const [analyticsLoading, setAnalyticsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  // Fetch the dates supported by the backend once.
  useEffect(() => {
    const controller = new AbortController()

    async function loadAvailability() {
      try {
        setError(null)

        const response = await fetch(
          `${API_BASE_URL}/api/analytics/availability`,
          { signal: controller.signal },
        )

        if (!response.ok) {
          throw new Error(
            `Availability request failed: ${response.status}`,
          )
        }

        const result: AvailabilityResponse = await response.json()
        setAvailability(result)

        if (result.available_dates.length > 0) {
          setSelectedDate(result.available_dates[0].delivery_date)
        }
      } catch (err) {
        if (err instanceof Error && err.name === 'AbortError') {
          return
        }

        setError(
          err instanceof Error
            ? err.message
            : 'An unexpected error occurred.',
        )
      } finally {
        if (!controller.signal.aborted) {
          setAvailabilityLoading(false)
        }
      }
    }

    void loadAvailability()

    return () => controller.abort()
  }, [])

  // Fetch analytics whenever the selected delivery date changes.
  useEffect(() => {
    if (!selectedDate) {
      return
    }

  const controller = new AbortController()

    async function loadAnalytics() {
      setAnalyticsLoading(true)
      setError(null)
      setData(null)

      try {
        const query = new URLSearchParams({
          delivery_date: selectedDate,
        })

        const response = await fetch(
          `${API_BASE_URL}/api/analytics/wind?${query.toString()}`,
          { signal: controller.signal },
        )

        if (!response.ok) {
          throw new Error(
            `Analytics request failed: ${response.status}`,
          )
        }

        const result: WindAnalyticsResponse = await response.json()
        setData(result)
      } catch (err) {
        if (err instanceof Error && err.name === 'AbortError') {
          return
        }

        setError(
          err instanceof Error
            ? err.message
            : 'An unexpected error occurred.',
        )
      } finally {
        if (!controller.signal.aborted) {
          setAnalyticsLoading(false)
        }
      }
    }

    void loadAnalytics()

    return () => controller.abort()
  }, [selectedDate])

  if (availabilityLoading) {
    return (
      <main className="grid min-h-screen place-items-center p-6 text-slate-600">
        <p>Loading available delivery dates…</p>
      </main>
    )
  }

  if (error && !availability) {
    return (
      <main className="mx-auto max-w-3xl p-6 sm:p-10">
        <h1 className="text-2xl font-bold tracking-tight text-slate-900">
          Wind forecast analytics
        </h1>

        <div
          role="alert"
          className="mt-6 rounded-xl border border-red-200 bg-red-50 p-4 text-sm text-red-800"
        >
          <p className="font-semibold">Unable to load available dates</p>
          <p className="mt-1">{error}</p>
          <p className="mt-2">
            Check that the FastAPI server is running and that the API URL is
            configured correctly.
          </p>
        </div>
      </main>
    )
  }

  if (!availability || availability.available_dates.length === 0) {
    return (
      <main className="mx-auto max-w-3xl p-6 sm:p-10">
        <h1 className="text-2xl font-bold tracking-tight text-slate-900">
          Wind forecast analytics
        </h1>
        <p className="mt-4 text-slate-600">
          No delivery dates currently have enough matched forecast and actual
          data for evaluation.
        </p>
      </main>
    )
  }

  const metrics = data
    ? [
        {
          label: 'Mean absolute error',
          value: formatMw(data.metrics.mae_mw),
          description: 'Average magnitude of forecast error',
        },
        {
          label: 'Root mean squared error',
          value: formatMw(data.metrics.rmse_mw),
          description: 'Penalizes larger errors more heavily',
        },
        {
          label: 'Forecast bias',
          value: formatMw(data.metrics.bias_mw),
          description:
            data.metrics.bias_mw === null
              ? 'No observations available'
              : data.metrics.bias_mw > 0
                ? 'Forecasts were higher on average'
                : data.metrics.bias_mw < 0
                  ? 'Forecasts were lower on average'
                  : 'No average signed error',
        },
        {
          label: 'Data coverage',
          value: `${data.coverage.evaluated_hours}/${data.coverage.expected_hours}`,
          description: `${data.coverage.evaluated_hours} of ${data.coverage.expected_hours} hours evaluated`,
        },
      ]
    : []

  return (
    <main className="min-h-screen px-4 py-8 sm:px-6 lg:px-10">
      <div className="mx-auto max-w-7xl">
        <DashboardHeader
          deliveryDate={data?.delivery_date ?? selectedDate}
          decisionCutoff={data?.decision_cutoff ?? ''}
          timezone={data?.timezone ?? 'Europe/London'}
        />

        <section
          aria-label="Delivery date selection"
          className="mt-6 rounded-xl border border-slate-200 bg-white p-4"
        >
          <label
            htmlFor="delivery-date"
            className="block text-sm font-medium text-slate-700"
          >
            Delivery date
          </label>

          <select
            id="delivery-date"
            value={selectedDate}
            onChange={(event) => setSelectedDate(event.target.value)}
            disabled={analyticsLoading}
            className="mt-2 block w-full max-w-sm rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-60"
          >
            {availability.available_dates.map((item) => (
              <option key={item.delivery_date} value={item.delivery_date}>
                {item.delivery_date}
              </option>
            ))}
          </select>
        </section>

        {error && (
          <div
            role="alert"
            className="mt-6 rounded-xl border border-red-200 bg-red-50 p-4 text-sm text-red-800"
          >
            <p className="font-semibold">Unable to load analytics</p>
            <p className="mt-1">{error}</p>
          </div>
        )}

        {analyticsLoading && (
          <p className="mt-6 text-sm text-slate-600" role="status">
            Loading analytics for {selectedDate}…
          </p>
        )}

        {data && !analyticsLoading && !error && (
          <>
            <section
              aria-label="Forecast summary metrics"
              className="mt-8 grid gap-4 sm:grid-cols-2 xl:grid-cols-4"
            >
              {metrics.map((metric) => (
                <MetricCard
                  key={metric.label}
                  label={metric.label}
                  value={metric.value}
                  description={metric.description}
                />
              ))}
            </section>

            <CoveragePanel coverage={data.coverage} />

            <GenerationChart data={data.hourly_data} />

            <HourlyGenerationTable
              hourlyData={data.hourly_data}
              observationCount={data.metrics.observation_count}
            />
          </>
        )}

        <footer className="py-6 text-xs text-slate-500">
          Wind forecast evaluation · UK delivery date · Cutoff-aware analysis
        </footer>
      </div>
    </main>
  )
}

export default App
