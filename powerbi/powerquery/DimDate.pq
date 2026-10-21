let
    Source = fxLoadCsv("dim_date.csv", {{"date", type date}, {"month", type text}, {"year", Int64.Type}, {"month_number", Int64.Type}})
in Source
