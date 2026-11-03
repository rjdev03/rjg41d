interface DashboardHeaderProps {
  deliveryDate: string
  decisionCutoff: string
  timezone: string
}

function DashboardHeader({
  deliveryDate,
  decisionCutoff,
  timezone,
}: DashboardHeaderProps) {
  return (
    <header className="flex flex-col gap-6 border-b border-slate-200 pb-8 lg:flex-row lg:items-end lg:justify-between">
      <div>
        <p className="text-xs font-bold uppercase tracking-[0.2em] text-blue-700">
           Wind analytics platform
        </p>

        <h1 className="mt-3 text-3xl font-bold tracking-tight text-slate-950 sm:text-4xl">
          Forecast performance
        </h1>

        <p className="mt-3 max-w-2xl text-sm leading-6 text-slate-600 sm:text-base">
          Compare forecast wind generation with actual output to understand
          forecast accuracy before delivery.
        </p>
      </div>

      <div className="grid gap-3 rounded-xl border border-slate-200 bg-white p-4 shadow-sm sm:grid-cols-2 lg:min-w-96 lg:grid-cols-1">
        <div>
          <p className="text-xs font-medium uppercase tracking-wide text-slate-500">
            Delivery date
          </p>

          <p className="mt-1 font-semibold text-slate-900">
            {deliveryDate}
          </p>
        </div>

        <div>
          <p className="text-xs font-medium uppercase tracking-wide text-slate-500">
            Decision cutoff
          </p>

          <p className="mt-1 font-semibold text-slate-900">
            {new Date(decisionCutoff).toLocaleString('en-GB', {
              dateStyle: 'medium',
              timeStyle: 'short',
              timeZone: timezone,
            })}{' '}
            UK time
          </p>
        </div>
      </div>
    </header>
  )
}

export default DashboardHeader
