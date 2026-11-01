import {
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'

import type { HourlyRecord } from '../types'

interface GenerationChartProps {
  data: HourlyRecord[]
}

function formatDeliveryTime(timestamp: string): string {
  return new Intl.DateTimeFormat('en-GB', {
    hour: '2-digit',
    minute: '2-digit',
    timeZone: 'Europe/London',
    hourCycle: 'h23',
  }).format(new Date(timestamp))
}

function formatMegawatts(value: number): string {
  return `${value.toLocaleString('en-GB', {
    maximumFractionDigits: 1,
  })} MW`
}

export default function GenerationChart({
  data,
}: GenerationChartProps) {
  const chartData = data.map((record) => ({
    ...record,
    delivery_label: formatDeliveryTime(record.delivery_time),
  }))

  if (chartData.length === 0) {
    return (
      <section className="rounded-xl border border-slate-200 bg-white p-6">
        <h2 className="text-lg font-semibold text-slate-900">
          Forecast vs actual generation
        </h2>
        <p className="mt-4 text-sm text-slate-500">
          No hourly generation data is available to display.
        </p>
      </section>
    )
  }

  return (
    <section className="rounded-xl border border-slate-200 bg-white p-6">
      <div className="mb-6">
        <h2 className="text-lg font-semibold text-slate-900">
          Forecast vs actual generation
        </h2>
        <p className="mt-1 text-sm text-slate-500">
          Hourly wind generation across the delivery day.
        </p>
      </div>

      <div className="h-80 w-full">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart
            data={chartData}
            margin={{ top: 8, right: 16, left: 16, bottom: 8 }}
          >
            <CartesianGrid
              strokeDasharray="3 3"
              vertical={false}
            />

            <XAxis
              dataKey="delivery_label"
              tick={{ fontSize: 12 }}
              tickLine={false}
              axisLine={false}
              interval="preserveStartEnd"
            />

            <YAxis
              tickFormatter={(value: number) =>
                value.toLocaleString('en-GB')
              }
              tick={{ fontSize: 12 }}
              tickLine={false}
              axisLine={false}
              width={75}
            />

            <Tooltip
              labelFormatter={(label) => `Delivery time: ${label}`}
              formatter={(value, name) => [
                formatMegawatts(Number(value)),
                name,
              ]}
            />

            <Legend />

            <Line
              type="monotone"
              dataKey="forecast_mw"
              name="Forecast"
              stroke="#2563eb"
              strokeWidth={2}
              dot={false}
              activeDot={{ r: 5 }}
            />

            <Line
              type="monotone"
              dataKey="actual_mw"
              name="Actual"
              stroke="#16a34a"
              strokeWidth={2}
              dot={false}
              activeDot={{ r: 5 }}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>

      <p className="mt-3 text-xs text-slate-500">
        Generation values are measured in megawatts (MW).
        Times are displayed in UK local time.
      </p>
    </section>
  )
}
