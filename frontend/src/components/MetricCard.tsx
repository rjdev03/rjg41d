interface MetricCardProps {
  label: string
  value: string
  description: string
}

function MetricCard({
  label,
  value,
  description,
}: MetricCardProps) {
  return (
    <article className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
      <p className="text-sm font-medium text-slate-600">
        {label}
      </p>

      <p className="mt-3 text-2xl font-bold tracking-tight text-slate-950">
        {value}
      </p>

      <p className="mt-2 text-xs leading-5 text-slate-500">
        {description}
      </p>
    </article>
  )
}

export default MetricCard
