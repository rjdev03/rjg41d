import type { HourlyRecord } from '../types'

interface HourlyGenerationTableProps {
  hourlyData: HourlyRecord[]
  observationCount: number
}

const numberFormatter = new Intl.NumberFormat('en-GB', {
  maximumFractionDigits: 1,
})

function HourlyGenerationTable({
  hourlyData,
  observationCount,
}: HourlyGenerationTableProps) {
  return (
    <section className="mt-8 overflow-hidden rounded-xl border border-slate-200 bg-white shadow-sm">
      <div className="flex flex-col gap-3 border-b border-slate-200 p-5 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h2 className="text-lg font-semibold text-slate-900">
            Hourly generation
          </h2>

          <p className="mt-1 text-sm text-slate-500">
            Forecast versus actual output, in megawatts.
          </p>
        </div>

        <span className="w-fit rounded-full bg-slate-100 px-3 py-1 text-xs font-medium text-slate-700">
          {observationCount} observations
        </span>
      </div>

      {hourlyData.length === 0 ? (
        <p className="p-6 text-sm text-slate-600">
          No matching forecast and actual-generation hours were found.
        </p>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full min-w-160 border-collapse text-left text-sm">
            <thead className="bg-slate-50 text-xs uppercase tracking-wide text-slate-500">
              <tr>
                <th scope="col" className="px-5 py-3 font-semibold">
                  Delivery time (UTC)
                </th>

                <th
                  scope="col"
                  className="px-5 py-3 text-right font-semibold"
                >
                  Forecast (MW)
                </th>

                <th
                  scope="col"
                  className="px-5 py-3 text-right font-semibold"
                >
                  Actual (MW)
                </th>

                <th
                  scope="col"
                  className="px-5 py-3 text-right font-semibold"
                >
                  Error (MW)
                </th>
              </tr>
            </thead>

            <tbody className="divide-y divide-slate-100">
              {hourlyData.map((hour) => (
                <tr
                  key={hour.delivery_time}
                  className="transition-colors hover:bg-slate-50"
                >
                  <td className="whitespace-nowrap px-5 py-3 font-medium text-slate-800">
                    {new Date(hour.delivery_time).toLocaleTimeString(
                      'en-GB',
                      {
                        hour: '2-digit',
                        minute: '2-digit',
                        timeZone: 'UTC',
                      },
                    )}
                  </td>

                  <td className="whitespace-nowrap px-5 py-3 text-right tabular-nums text-slate-700">
                    {numberFormatter.format(hour.forecast_mw)}
                  </td>

                  <td className="whitespace-nowrap px-5 py-3 text-right tabular-nums text-slate-700">
                    {numberFormatter.format(hour.actual_mw)}
                  </td>

                  <td
                    className={`whitespace-nowrap px-5 py-3 text-right font-semibold tabular-nums ${
                      hour.error_mw > 0
                        ? 'text-amber-700'
                        : hour.error_mw < 0
                          ? 'text-blue-700'
                          : 'text-slate-700'
                    }`}
                  >
                    {hour.error_mw > 0 ? '+' : ''}
                    {numberFormatter.format(hour.error_mw)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      <div className="border-t border-slate-200 bg-slate-50 px-5 py-4">
        <p className="text-xs leading-5 text-slate-600">
          Error = forecast minus actual. Positive values indicate
          over-forecasting; negative values indicate under-forecasting.
          This dashboard evaluates forecast accuracy; it does not
          calculate procurement requirements.
        </p>
      </div>
    </section>
  )
}

export default HourlyGenerationTable
