"""Author the report using the checked-in official CLI scaffold and public PBIR format."""
from pathlib import Path
import csv
import json
import uuid

from pbir_helpers import BASE, color, configure, field, literal, projection, textbox, visual, write

ROOT=Path(__file__).resolve().parents[1]
PBI=ROOT/'powerbi'
REPORT=PBI/'LogisticsDelivery.Report'
MODEL=PBI/'LogisticsDelivery.SemanticModel'
NAVY='#132A3A'
TEAL='#007F7A'

MEASURES={
 'Cohort Orders':'COUNTROWS(FactDelivery)',
 'Eligible Deliveries':'SUM(FactDelivery[eligible_flag])',
 'Delivered Status Orders':'SUM(FactDelivery[delivered_flag])',
 'Late Deliveries':'SUM(FactDelivery[late_flag])',
 'On Time Deliveries':'[Eligible Deliveries] - [Late Deliveries]',
 'On Time Delivery %':'DIVIDE([On Time Deliveries], [Eligible Deliveries])',
 'Late Delivery %':'DIVIDE([Late Deliveries], [Eligible Deliveries])',
 'Eligibility Coverage %':'DIVIDE([Eligible Deliveries], [Cohort Orders])',
 'Median Delivery Days':'DIVIDE(MEDIAN(FactDelivery[delivery_seconds]), 86400)',
 'P90 Delivery Days':'IF([Eligible Deliveries] > 0, PERCENTILEX.INC(FILTER(FactDelivery, FactDelivery[eligible_flag] = 1), FactDelivery[delivery_seconds] / 86400.0, 0.9))',
 'Mean Processing Days':'DIVIDE(AVERAGE(FactDelivery[processing_seconds]), 86400)',
 'Mean Post Handover Days':'DIVIDE(AVERAGE(FactDelivery[post_handover_seconds]), 86400)',
 'Complete Stage Orders':'SUM(FactDelivery[stage_valid_flag])',
 'Stage Coverage %':'DIVIDE([Complete Stage Orders], [Eligible Deliveries])',
 'Severe Late Deliveries':'SUM(FactDelivery[severe_late_flag])',
 'Reviewed Eligible Orders':'SUM(FactDelivery[reviewed_eligible_flag])',
 'Low Score Orders':'SUM(FactDelivery[poor_review_flag])',
 'Low Score %':'DIVIDE([Low Score Orders], [Reviewed Eligible Orders])',
 'Review Coverage %':'DIVIDE([Reviewed Eligible Orders], [Eligible Deliveries])',
 'Noneligible Orders':'[Cohort Orders] - [Eligible Deliveries]',
 'Previous Month OTD %':'CALCULATE([On Time Delivery %], DATEADD(DimDate[date], -1, MONTH))',
 'OTD Change pp':'IF(NOT ISBLANK([Previous Month OTD %]), 100 * ([On Time Delivery %] - [Previous Month OTD %]))',
 'Top Eight State Late Orders':'IF(SELECTEDVALUE(DimState[late_volume_rank], 999) <= 8, [Late Deliveries])',
 'Comparable Category Late %':'IF([Eligible Deliveries] >= 100, [Late Delivery %])'
}


def lineage(name): return str(uuid.uuid5(uuid.NAMESPACE_URL,'james-you/logistics/'+name))


def build_model():
    integers={'item_count','seller_count','eligible_flag','delivered_flag','late_flag','severe_late_flag','late_days',
      'delivery_seconds','processing_seconds','post_handover_seconds','stage_valid_flag','review_score','valid_review_count',
      'reviewed_eligible_flag','poor_review_flag','priority_rank','merchandise_cents','freight_cents'}
    with (ROOT/'data/processed/fact_delivery.csv').open() as source:
        headers=next(csv.reader(source))
    schemas={
      'FactDelivery':[(name,'int64' if name in integers else 'dateTime' if name=='purchase_date' else 'string') for name in headers],
      'DimDate':[('date','dateTime'),('month','string'),('year','int64'),('month_number','int64')],
      'DimState':[('customer_state','string'),('late_volume_rank','int64')],
      'DimCategory':[('category','string'),('category_label','string')]
    }
    sources={'FactDelivery':'fact_delivery.csv','DimDate':'dim_date.csv','DimState':'dim_state.csv','DimCategory':'dim_category.csv'}
    pq=PBI/'powerquery';pq.mkdir(exist_ok=True)
    function='''(FileName as text, ColumnTypes as list) as table =>
let
    Source = Csv.Document(File.Contents(pDataFolder & FileName), [Delimiter=",", Encoding=65001, QuoteStyle=QuoteStyle.Csv]),
    Headers = Table.PromoteHeaders(Source, [PromoteAllScalars=true]),
    EmptyToNull = Table.ReplaceValue(Headers, "", null, Replacer.ReplaceValue, Table.ColumnNames(Headers)),
    Typed = Table.TransformColumnTypes(EmptyToNull, ColumnTypes, "en-GB")
in Typed
'''
    (pq/'fxLoadCsv.pq').write_text(function)
    tables=[]
    for table,fields in schemas.items():
        types=', '.join('{"'+name+'", '+('Int64.Type' if typ=='int64' else 'type date' if typ=='dateTime' else 'type text')+'}' for name,typ in fields)
        m='let\n    Source = fxLoadCsv("'+sources[table]+'", {'+types+'})\nin Source\n'
        (pq/(table+'.pq')).write_text(m)
        columns=[]
        for name,typ in fields:
            column={'name':name,'sourceColumn':name,'dataType':typ,'summarizeBy':'none','lineageTag':lineage(table+'/'+name)}
            if typ=='dateTime':column['formatString']='yyyy-MM-dd'
            if typ=='int64':column['formatString']='#,0'
            if table=='FactDelivery' and name.endswith(('_flag','_seconds','_cents')):column['isHidden']=True
            if (table,name) in [('DimDate','date'),('DimState','customer_state'),('DimCategory','category')]:column['isKey']=True
            columns.append(column)
        item={'name':table,'lineageTag':lineage(table),'columns':columns,
          'partitions':[{'name':table,'mode':'import','source':{'type':'m','expression':m}}],
          'annotations':[{'name':'PBI_ResultType','value':'Table'}]}
        if table=='DimDate':item['dataCategory']='Time'
        if table=='FactDelivery':
            item['measures']=[{'name':name,'expression':expression,'lineageTag':lineage('measure/'+name),
              'formatString':'0.00%' if name.endswith('%') else '0.00" pp"' if name.endswith(' pp') else '0.00' if 'Days' in name else '#,0',
              'displayFolder':'Delivery service' if 'Review' not in name and 'Score' not in name else 'Feedback and evidence'} for name,expression in MEASURES.items()]
        tables.append(item)
    relations=[]
    for source,target,key in [('purchase_date','DimDate','date'),('customer_state','DimState','customer_state'),('category','DimCategory','category')]:
        relations.append({'name':lineage('relationship/'+source),'fromTable':'FactDelivery','fromColumn':source,
          'toTable':target,'toColumn':key,'fromCardinality':'many','toCardinality':'one','crossFilteringBehavior':'oneDirection','isActive':True})
    model={'name':'LogisticsDelivery','compatibilityLevel':1567,'model':{
      'culture':'en-GB','sourceQueryCulture':'en-GB','defaultPowerBIDataSourceVersion':'powerBI_V3',
      'tables':tables,'relationships':relations,'expressions':[
        {'name':'pDataFolder','kind':'m','expression':'"C:/LogisticsDelivery/data/processed/" meta [IsParameterQuery=true, Type="Text", IsParameterQueryRequired=true]'},
        {'name':'fxLoadCsv','kind':'m','expression':function}],
      'annotations':[{'name':'PBI_TimeIntelligenceEnabled','value':'0'},
        {'name':'PortfolioScope','value':'Public Olist historical order outcomes. No observed damage/loss or carrier attribution.'}]}}
    write(MODEL/'model.bim',model)
    write(MODEL/'definition.pbism',{'$schema':BASE+'item/semanticModel/definitionProperties/1.0.0/schema.json','version':'1.0','settings':{'qnaEnabled':False}})
    (PBI/'measures.dax').write_text('// Source definitions; Desktop execution is confirmed separately.\n\n'+'\n\n'.join(k+' =\n'+v for k,v in MEASURES.items())+'\n')


def pcol(table,name,display=None):return projection(table,name,False,display)
def pmeasure(name,display=None):return projection('FactDelivery',name,True,display)


def slicer(page,name,table,prop,label,x,y,w):
    visual(page,name,'slicer',x,y,w,80,'',{'Values':[pcol(table,prop)]},objects={
      'data':[{'properties':{'mode':literal('Dropdown')}}],
      'header':[{'properties':{'show':literal(True),'text':literal(label)}}]})
    path=REPORT/'definition/pages'/page/'visuals'/name/'visual.json'
    obj=json.loads(path.read_text())
    obj['visual']['visualContainerObjects']['padding']=[{'properties':{name:literal(8) for name in ['top','bottom','left','right']}}]
    write(path,obj)


def header(page,title,subtitle):
    textbox(page,'Header',title,24,16,1232,70,24,'#FFFFFF',NAVY)
    textbox(page,'Scope',subtitle,24,94,1232,38,11,'#586D7C')


def common_filters(page):
    slicer(page,'Month','DimDate','month','Purchase month',24,140,210)
    slicer(page,'Destination','DimState','customer_state','Destination state',252,140,190)
    slicer(page,'Category','DimCategory','category_label','Order category',460,140,490)
    slicer(page,'Route','FactDelivery','route_type','Seller-state route type',968,140,288)


def cards(page,definitions,y=238):
    for i,(name,label) in enumerate(definitions):
        visual(page,'Card'+str(i),'card',24+314*i,y,290,110,label,{'Values':[pmeasure(name)]},objects={
          'labels':[{'properties':{'fontSize':literal(28),'labelDisplayUnits':literal(1),'color':color(NAVY)}}],
          'categoryLabels':[{'properties':{'show':literal(False)}}]})


def build_report():
    configure(REPORT)
    # The project shell and theme resources are checked-in outputs of Microsoft's
    # CLI 0.5.0 scaffold; preserve their format contracts when authoring visuals.
    meta=json.loads((REPORT/'definition/report.json').read_text())
    meta['annotations']=[{'name':'ValidationScope','value':'Public schema and runtime checks are separate from owner-run Windows Desktop validation.'}]
    write(REPORT/'definition/report.json',meta)
    pages=[('DeliveryOverview','01 Delivery Overview'),('DelayInvestigation','02 Delay Investigation'),('ReviewActions','03 Review & Actions')]
    write(REPORT/'definition/pages/pages.json',{'$schema':BASE+'item/report/definition/pagesMetadata/1.1.0/schema.json','pageOrder':[p for p,_ in pages],'activePageName':pages[0][0]})
    for page,label in pages:
        write(REPORT/'definition/pages'/page/'page.json',{'$schema':BASE+'item/report/definition/page/2.1.0/schema.json',
          'name':page,'displayName':label,'displayOption':'FitToPage','height':960,'width':1280,
          'objects':{'background':[{'properties':{'color':color('#F2F6F8'),'transparency':literal(0)}}]}})
    p='DeliveryOverview'
    header(p,'DELIVERY RELIABILITY | SERVICE REVIEW','James You | Olist public historical orders | Purchase cohort Jan 2017 - Jun 2018 | Calendar-date promise rule')
    common_filters(p)
    cards(p,[('Eligible Deliveries','Eligible delivered orders'),('On Time Delivery %','On-time delivery'),('Late Deliveries','Late deliveries'),('P90 Delivery Days','P90 purchase-to-delivery days')])
    visual(p,'MonthlyOTD','lineChart',24,366,750,270,'Monthly on-time delivery - eligible delivered denominator',
      {'Category':[pcol('DimDate','month')],'Y':[pmeasure('On Time Delivery %')]},(field('DimDate','month'),'Ascending'))
    visual(p,'StateLate','barChart',792,366,464,270,'Top 8 baseline states - late orders in selection',
      {'Category':[pcol('DimState','customer_state')],'Y':[pmeasure('Top Eight State Late Orders')]},(field('FactDelivery','Top Eight State Late Orders',True),'Descending'))
    textbox(p,'Decisions','BASELINE REVIEW EXAMPLE\nFull-cohort SP to RJ: 1,120 late deliveries among 7,201 eligible single-seller orders (15.55%).\nInvestigate both processing and post-handover stages; timestamps alone do not establish fault.\nSeparate data defects from service exceptions and record follow-up evidence.',24,654,750,226,14)
    textbox(p,'Denominator','FULL BASELINE AND COVERAGE\n86,288 purchase-cohort orders; 83,696 qualify for delivery performance. Cards above follow the current selection.\nCancelled, unavailable, missing or contradictory records are outside the on-time denominator.\nThese are final recorded historical outcomes.',792,654,464,226,12)
    textbox(p,'Footer','Source: Olist / Kaggle | CC BY-NC-SA 4.0 | Historical Brazil data | No realised improvement or carrier/damage/loss claim.',24,904,1232,36,10,'#586D7C')

    p='DelayInvestigation'
    header(p,'DELAY INVESTIGATION | TIMELINE & FEEDBACK','All stages use one complete valid-timestamp cohort. Customer scores indicate association, not proven delay causation.')
    common_filters(p)
    cards(p,[('Mean Processing Days','Mean purchase-to-handover days'),('Mean Post Handover Days','Mean handover-to-delivery days'),('Stage Coverage %','Stage timestamp coverage'),('Review Coverage %','Review coverage of eligible orders')])
    visual(p,'Stages','barChart',24,366,600,270,'Elapsed stage days by delivery outcome - joint valid cohort',
      {'Category':[pcol('FactDelivery','late_band')],'Y':[pmeasure('Mean Processing Days'),pmeasure('Mean Post Handover Days')]})
    visual(p,'Feedback','barChart',642,366,614,270,'Low review scores (1-2) among reviewed eligible orders',
      {'Category':[pcol('FactDelivery','late_band')],'Y':[pmeasure('Low Score %')]})
    visual(p,'CategoryTable','tableEx',24,654,860,226,'Category comparisons - rates shown at n >= 100 eligible orders',
      {'Values':[pcol('DimCategory','category_label','Category'),pmeasure('Eligible Deliveries','Eligible orders'),
        pmeasure('Late Deliveries','Late orders'),pmeasure('Comparable Category Late %','Late % (n>=100)'),pmeasure('P90 Delivery Days','P90 days')]},
      (field('FactDelivery','Late Deliveries',True),'Descending'))
    textbox(p,'Interpretation','INVESTIGATE BEFORE ATTRIBUTING\nOrder timestamps do not identify the responsible carrier, route disruption or damage/loss event.\nObtain scan events, reasons, parcel/seller mapping and promised-service definitions before assigning corrective action.',902,654,354,226,12)
    textbox(p,'Footer','Multiple sellers are labelled explicitly. Source dates have no supplied timezone; elapsed times use recorded timestamps.',24,904,1232,36,10,'#586D7C')

    p='ReviewActions'
    header(p,'HISTORICAL EXCEPTIONS | REVIEW TO ACTION','Investigation records are historical examples. The proposed workflow and owners are recommendations, not an implemented intervention.')
    slicer(p,'Month','DimDate','month','Purchase month',24,140,210)
    slicer(p,'Destination','DimState','customer_state','Destination state',252,140,190)
    slicer(p,'Priority','FactDelivery','review_priority','Review priority',460,140,490)
    slicer(p,'Case','FactDelivery','case_code','Example case code',968,140,288)
    cards(p,[('Cohort Orders','Orders in selection'),('Late Deliveries','Late deliveries'),('Severe Late Deliveries','Over 7 days late'),('Noneligible Orders','Outside delivery denominator')])
    visual(p,'CaseTable','tableEx',24,366,1232,326,'Order-grain historical review records - most days late first',
      {'Values':[pcol('FactDelivery','case_code','Case'),pcol('FactDelivery','purchase_date','Purchased'),
        pcol('DimState','customer_state','State'),pcol('FactDelivery','review_priority','Review priority'),
        pcol('FactDelivery','late_days','Days late'),pcol('FactDelivery','review_score','Score'),pcol('DimCategory','category_label','Category')]},
      (field('FactDelivery','late_days'),'Descending'))
    textbox(p,'Workflow','PROPOSED REVIEW WORKFLOW\n1. Reporting analyst reconciles the cohort, exceptions and timestamp defects.\n2. Fulfilment lead validates dispatch/scan evidence for high-volume delay groups.\n3. Logistics operations verifies post-handover reasons and parcel/carrier mapping.\n4. Customer experience team reviews affected communications and promise wording.\n5. Owners record action, due date and evidence; monitor service rate, volume and review closure.',24,710,790,170,12)
    textbox(p,'Success','ACCEPTANCE AND FOLLOW-UP\nBaseline -> verify evidence -> pilot -> compare like-for-like cohorts.\nTrack data completeness, review closure and delivery performance.\nNo savings or service improvement is claimed from this historical case.',832,710,424,170,12)
    textbox(p,'Footer','See docs/business_requirements.md and docs/UAT.md for traceable requirements, acceptance cases and a proposed pilot.',24,904,1232,36,10,'#586D7C')


def main():
    build_model();build_report()
    print(json.dumps({'status':'AUTHORED','pages':3,'visuals':len(list(REPORT.rglob('visual.json'))),'tables':4,'measures':len(MEASURES),
      'desktop_status':'Requires owner Windows refresh and visual confirmation'}))


if __name__=='__main__':main()
