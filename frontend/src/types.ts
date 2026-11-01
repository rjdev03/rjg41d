export interface WindMetrics {
  observation_count: number
  mae_mw: number | null
  rmse_mw: number | null
  bias_mw: number | null
}

export interface Coverage {
  expected_hours: number
  forecast_hours_available: number
  actual_hours_available: number
  evaluated_hours: number
  missing_forecast_hours: number
  missing_actual_hours: number
}

export interface HourlyRecord {
  delivery_time: string
  forecast_mw: number
  actual_mw: number
  error_mw: number
}

export interface WindAnalyticsResponse {
  delivery_date: string
  decision_cutoff: string
  timezone: string
  coverage: Coverage
  metrics: WindMetrics
  hourly_data: HourlyRecord[]
}

export interface AvailableDeliveryDate {
  delivery_date: string
  expected_hours: number
  actual_hours_available: number
  forecast_hours_available: number
  evaluated_hours: number
}

export interface AvailabilityResponse {
  available_dates: AvailableDeliveryDate[]
}
