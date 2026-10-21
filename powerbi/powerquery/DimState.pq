let
    Source = fxLoadCsv("dim_state.csv", {{"customer_state", type text}, {"late_volume_rank", Int64.Type}})
in Source
