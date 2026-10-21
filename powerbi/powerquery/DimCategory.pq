let
    Source = fxLoadCsv("dim_category.csv", {{"category", type text}, {"category_label", type text}})
in Source
