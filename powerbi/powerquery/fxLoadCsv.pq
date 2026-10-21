(FileName as text, ColumnTypes as list) as table =>
let
    Source = Csv.Document(File.Contents(pDataFolder & FileName), [Delimiter=",", Encoding=65001, QuoteStyle=QuoteStyle.Csv]),
    Headers = Table.PromoteHeaders(Source, [PromoteAllScalars=true]),
    EmptyToNull = Table.ReplaceValue(Headers, "", null, Replacer.ReplaceValue, Table.ColumnNames(Headers)),
    Typed = Table.TransformColumnTypes(EmptyToNull, ColumnTypes, "en-GB")
in Typed
