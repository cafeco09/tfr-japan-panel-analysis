import fs from 'node:fs/promises';
import { Workbook, SpreadsheetFile } from '@oai/artifact-tool';

const root=process.argv[2];
const outputDir=process.argv[3];
if(!root||!outputDir)throw new Error('Provide repository root and output directory');
const data=JSON.parse(await fs.readFile(`${root}/output/food_names/workbook_data.json`,'utf8'));
await fs.mkdir(outputDir,{recursive:true});
const wb=Workbook.create();
const foods=wb.worksheets.add('Food names');
const annual=wb.worksheets.add('Annual groups');
const soy=wb.worksheets.add('Soyabeans');
const raw=wb.worksheets.add('Sources');
const inputs=wb.worksheets.add('Summary inputs');
inputs.getRange('A1:C1').values=[['HS4','2025 USD','Returned products']];
inputs.getRange(`A2:C${1+data.latest.length}`).values=data.latest.map(r=>[r.hs4,r.import_value_current_usd,r.returned_product_codes]);
const categories=[...new Set(data.groups.map(r=>r.hs2))].sort();
inputs.getRange('E1:O1').values=[['HS2',...Array.from({length:10},(_,i)=>2016+i)]];
inputs.getRange(`E2:O${1+categories.length}`).values=categories.map(c=>[c,...Array.from({length:10},(_,i)=>data.groups.find(r=>r.hs2===c&&r.year===2016+i)?.import_value_current_usd??'n.a.')]);
inputs.getRange('Q1:AA1').values=[['HS6',...Array.from({length:10},(_,i)=>2016+i)]];
inputs.getRange('Q2:AA8').values=data.soy_definitions.map(d=>[d.hs6,...Array.from({length:10},(_,i)=>{const found=data.products.filter(r=>r.hs6===d.hs6&&r.year===2016+i);return found.length?found.reduce((a,r)=>a+r.import_value_current_usd,0):'n.a.';})]);
inputs.getRange('A160').values=[['Inputs aggregated by _16_named_food_imports.py from Products; see CSVs and provenance.']];
const blue='#233F5D',pale='#EAF0F5',ink='#182C3D',muted='#526575',amber='#FFF2CC';
const last=5+data.products.length;
const R={year:`Products!$A$6:$A$${last}`,chapter:`Products!$C$6:$C$${last}`,
         heading:`Products!$E$6:$E$${last}`,code:`Products!$G$6:$G$${last}`,
         included:`Products!$J$6:$J$${last}`,value:`Products!$K$6:$K$${last}`};
function base(sheet,range){
  sheet.showGridLines=false;
  sheet.getRange(range).format.font={name:'Arial',size:10,color:ink};
  sheet.getRange(range).format.verticalAlignment='center';
  sheet.getRange(range).format.rowHeight=21;
}
function heading(sheet,range){sheet.getRange(range).format={fill:blue,font:{name:'Arial',size:10,bold:true,color:'#FFFFFF'},horizontalAlignment:'center',verticalAlignment:'center',wrapText:true,rowHeight:32};}
function title(sheet,address,text){sheet.getRange(address).values=[[text]];sheet.getRange(address).format.font={name:'Arial',size:15,bold:true,color:ink};sheet.getRange(address).format.rowHeight=26;}
function note(sheet,address,text){sheet.getRange(address).values=[[text]];sheet.getRange(address).format.font={name:'Arial',size:10,italic:true,color:muted};}

base(inputs,'A1:AA160');
for(const r of ['A1:C1','E1:O1','Q1:AA1'])heading(inputs,r);
inputs.getRange('A:AA').format.columnWidth=19;
inputs.getRange('B2:B155').setNumberFormat('#,##0');
inputs.getRange('F2:O22').setNumberFormat('#,##0');
inputs.getRange('R2:AA8').setNumberFormat('#,##0');
inputs.getRange('A2:A155').setNumberFormat('0000');
inputs.getRange('E2:E22').setNumberFormat('00');
inputs.getRange('Q2:Q8').setNumberFormat('000000');
inputs.freezePanes.freezeRows(1);
base(raw,'A1:X100');
title(raw,'A1','Sources and published totals');
note(raw,'A2','Full HS6 records: output/food_names/named_food_products_2016_2025.csv in the repository.');
note(raw,'A4','Full query URLs are retained by source batch in output/food_names/source_batches.csv.');
note(raw,'A3','Summary inputs are upstream aggregations from the full product CSV, not individual consumption.');
raw.getRange('A5:E5').values=[['Source batch','Year','HS edition','Source URL','Retrieved UTC']];heading(raw,'A5:E5');
raw.getRange(`A6:E${5+data.sources.length}`).values=data.sources.map(r=>[r.batch_id,r.year,r.revision,r.source_url.split('?')[0],r.retrieved_utc]);
raw.getRange('A:A').format.columnWidth=23;raw.getRange('B:C').format.columnWidth=12;
raw.getRange('D:D').format.columnWidth=65;raw.getRange('E:E').format.columnWidth=31;
raw.getRange('G5:H5').values=[['Year','Published BEC food (USD)']];heading(raw,'G5:H5');
raw.getRange('G6:H15').values=data.reconciliation.map(r=>[r.year,r.external_food_import_value_current_usd]);
raw.getRange('G:G').format.columnWidth=12;raw.getRange('H:H').format.columnWidth=25;raw.getRange('H6:H15').setNumberFormat('#,##0');
raw.getRange(`E6:E${5+data.sources.length}`).setNumberFormat('yyyy-mm-dd hh:mm');
raw.getRange(`D6:D${5+data.sources.length}`).format.wrapText=false;
raw.getRange(`A6:E${5+data.sources.length}`).format.rowHeight=24;
raw.freezePanes.freezeRows(5);
// Raw records remain a filter-free source range for export compatibility.

const end=5+data.latest.length,total=end+2;
base(foods,`B1:G${total+5}`);foods.tabColor=blue;
title(foods,'B2','Japan’s imported foods by name');
note(foods,'B3','All origins. 2025 values in current USD. Shares refer to mapped food records.');
note(foods,'B4','Official BEC food includes some non-dietary uses; scope exceptions are flagged.');
foods.getRange('B5:G5').values=[['HS4','Food name','Import value (USD)','Share of mapped food','HS6 products','Scope note']];heading(foods,'B5:G5');
data.latest.forEach((r,i)=>{
  const row=i+6;
  foods.getRange(`B${row}:C${row}`).values=[[r.hs4,r.food_name]];
  foods.getRange(`D${row}`).formulas=[[`='Summary inputs'!B${i+2}`]];
  foods.getRange(`E${row}`).formulas=[[`=D${row}/$D$${total}`]];
  foods.getRange(`F${row}`).formulas=[[`='Summary inputs'!C${i+2}`]];
  const notes=r.hs4==='1201'?'Includes seed for sowing. See Soyabeans.':r.hs4==='2404'?'Oral nicotine products: review food boundary.':r.hs4.startsWith('23')?'Milling/food-industry residues; possible feed use.':r.hs4.startsWith('01')?'Live animals; final use is not established.':r.hs4.startsWith('35')?'Albumins/enzymes; includes industrial ingredients.':'';
  foods.getRange(`G${row}`).values=[[notes]];
  if(notes)foods.getRange(`G${row}`).format.fill=amber;
});
foods.getRange(`C${total}:C${total+2}`).values=[['Mapped food total'],['Published World BEC food total'],['Mapped minus published total']];
foods.getRange(`D${total}:D${total+2}`).formulas=[[`=SUM(D6:D${end})`],[`=Sources!H15`],[`=D${total}-D${total+1}`]];
foods.getRange(`B${total}:F${total}`).format.fill=pale;foods.getRange(`C${total}:D${total+2}`).format.font.bold=true;
foods.getRange(`B6:B${end}`).setNumberFormat('0000');foods.getRange(`D6:D${total+2}`).setNumberFormat('#,##0');foods.getRange(`E6:E${end}`).setNumberFormat('0.00%');foods.getRange(`F6:F${end}`).setNumberFormat('0');
foods.getRange('B:B').format.columnWidth=10;foods.getRange('C:C').format.columnWidth=78;foods.getRange('D:D').format.columnWidth=24;foods.getRange('E:E').format.columnWidth=23;foods.getRange('F:F').format.columnWidth=15;foods.getRange('G:G').format.columnWidth=61;
foods.getRange(`C6:C${end}`).format.wrapText=true;foods.getRange(`B6:G${end}`).format.rowHeight=32;
data.latest.forEach((r,i)=>{foods.getRange(`B${i+6}:G${i+6}`).format.rowHeight=Math.max(32,16*Math.ceil(r.food_name.length/70)+6);});
foods.freezePanes.freezeRows(5);

const groupMap=new Map();for(const r of data.groups)groupMap.set(r.hs2,r.food_group);
const groupRows=[...groupMap].sort((a,b)=>a[0].localeCompare(b[0]));
const gEnd=5+groupRows.length;
base(annual,`B1:M${gEnd+6}`);annual.tabColor=blue;
title(annual,'B2','Food categories across years');note(annual,'B3','All origins. Current USD. Only products mapped to BEC food are summed.');
note(annual,'B4','n.a. means no returned in-scope records; it is not an assumed zero.');
annual.getRange('B5:M5').values=[['HS2','Food category',...Array.from({length:10},(_,i)=>2016+i)]];heading(annual,'B5:M5');
groupRows.forEach(([code,name],i)=>{
  const row=6+i;annual.getRange(`B${row}:C${row}`).values=[[code,name]];
  for(let j=0;j<10;j++){
    const col=String.fromCharCode(68+j);
    annual.getRange(`${col}${row}`).formulas=[[`='Summary inputs'!${String.fromCharCode(70+j)}${i+2}`]];
  }
});
const gt=gEnd+2;
annual.getRange(`C${gt}:C${gt+2}`).values=[['Mapped food total'],['Published World BEC food total'],['Mapped minus published total']];
for(let j=0;j<10;j++){
  const col=String.fromCharCode(68+j);annual.getRange(`${col}${gt}:${col}${gt+2}`).formulas=[[`=SUM(${col}6:${col}${gEnd})`],[`=Sources!H${6+j}`],[`=${col}${gt}-${col}${gt+1}`]];
}
annual.getRange('B:B').format.columnWidth=10;annual.getRange('C:C').format.columnWidth=68;annual.getRange('D:M').format.columnWidth=21;
annual.getRange(`D6:M${gt+2}`).setNumberFormat('#,##0');annual.getRange(`B6:B${gEnd}`).setNumberFormat('00');
annual.getRange(`B${gt}:M${gt}`).format.fill=pale;annual.freezePanes.freezeRows(5);annual.freezePanes.freezeColumns(3);

base(soy,'B1:O20');soy.tabColor=blue;title(soy,'B2','Soyabeans and related products');
note(soy,'B3','All origins. Current USD. Soyabean oilcake is a separate non-food reference.');
note(soy,'B4','n.a. means no record returned. Product names do not establish actual end use.');
soy.getRange('B5:O5').values=[['HS6','Product','BEC food?',...Array.from({length:10},(_,i)=>2016+i),'Scope note']];heading(soy,'B5:O5');
data.soy_definitions.forEach((r,i)=>{
  const row=6+i;soy.getRange(`B${row}:D${row}`).values=[[r.hs6,r.name,r.included?'Yes':'No']];
  for(let j=0;j<10;j++){
    const col=String.fromCharCode(69+j);
    soy.getRange(`${col}${row}`).formulas=[[`='Summary inputs'!${j<9?String.fromCharCode(82+j):'AA'}${i+2}`]];
  }
  soy.getRange(`O${row}`).values=[[r.hs6==='230400'?'Outside BEC food. Excluded from food totals.':r.hs6==='120110'?'Seed for sowing.':'Source food classification; consumption not measured.']];
  if(!r.included)soy.getRange(`B${row}:O${row}`).format.fill=amber;
});
soy.getRange('B:B').format.columnWidth=12;soy.getRange('C:C').format.columnWidth=51;soy.getRange('D:D').format.columnWidth=13;soy.getRange('E:N').format.columnWidth=21;soy.getRange('O:O').format.columnWidth=62;
soy.getRange('B6:B12').setNumberFormat('000000');soy.getRange('E6:N12').setNumberFormat('#,##0');soy.freezePanes.freezeRows(5);soy.freezePanes.freezeColumns(4);
soy.getRange('C6:C12').format.wrapText=true;soy.getRange('B6:O12').format.rowHeight=34;

wb.recalculate();
console.log((await wb.inspect({kind:'table',range:'Food names!B5:F14',include:'values,formulas',tableMaxRows:10,tableMaxCols:5,maxChars:3000})).ndjson);
console.log((await wb.inspect({kind:'match',searchTerm:'#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A|#NUM!|#NULL!',options:{useRegex:true,maxResults:20},summary:'formula scan',maxChars:2000})).ndjson);
const exports={mainTotals:foods.getRange(`D${total}:D${total+2}`).values,
               annualTotals:annual.getRange(`D${gt}:M${gt+2}`).values,
               mainValues:foods.getRange(`D6:F${end}`).values,
               soyValues:soy.getRange('E6:N12').values};
await fs.writeFile(`${outputDir}/verification.json`,JSON.stringify(exports));
const xlsx=await SpreadsheetFile.exportXlsx(wb);
await xlsx.save(`${outputDir}/imported_food_names.xlsx`);
for(const [sheetName,range] of [['Food names','B1:F17'],['Annual groups','B1:G15'],['Soyabeans','B1:H13'],['Sources','A1:E14'],['Summary inputs','A1:C14']]){
  const preview=await wb.render({sheetName,range,scale:1.5,format:'png'});
  await fs.writeFile(`${outputDir}/${sheetName.replaceAll(' ','_')}.png`,new Uint8Array(await preview.arrayBuffer()));
}
console.log('Exported imported_food_names.xlsx');
