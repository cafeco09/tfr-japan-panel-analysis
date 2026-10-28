import fs from 'node:fs/promises';
import {FileBlob, SpreadsheetFile} from '@oai/artifact-tool';

const [input,payloadPath,outputDir,mode]=process.argv.slice(2);
const wb=await SpreadsheetFile.importXlsx(await FileBlob.load(input));
await fs.mkdir(outputDir,{recursive:true});
if(mode==='preview'){
  const preview=await wb.render({sheetName:'Annual groups',range:'B1:G12',scale:1.5,format:'png'});
  await fs.writeFile(`${outputDir}/before.png`,new Uint8Array(await preview.arrayBuffer()));
  console.log((await wb.inspect({kind:'table',range:'Annual groups!B5:G8',include:'values,formulas',maxChars:1800,tableMaxRows:4,tableMaxCols:6})).ndjson);
}else{
  const data=JSON.parse(await fs.readFile(payloadPath,'utf8'));
  const source=wb.worksheets.add('Prefecture TFR');source.showGridLines=false;
  source.getRange('A1').values=[['Official prefectural TFR source records']];
  source.getRange('A2').values=[['47 prefectures, 2016–2025. 2025 rates are provisional. Source URLs and cells are retained.']];
  source.getRange('A5:H5').values=[['Region code','Prefecture','Japanese name','Year','TFR','Release status','Source URL','Source cell']];
  source.getRange('A6:H475').values=data.tfr.map(r=>[r.region_code,r.prefecture,r.prefecture_japanese,r.year,r.tfr_children_per_woman,r.tfr_release_status,r.tfr_source,r.tfr_source_cell]);
  source.getRange('A1:H475').format.font={name:'Arial',size:10,color:'#182C3D'};
  source.getRange('A1:H475').format.rowHeight=26;source.getRange('A1:H475').format.verticalAlignment='center';
  source.getRange('A5:H5').format={fill:'#233F5D',font:{name:'Arial',size:10,bold:true,color:'#FFFFFF'},rowHeight:32,wrapText:true};
  source.getRange('A:A').format.columnWidth=14;source.getRange('B:C').format.columnWidth=21;
  source.getRange('D:D').format.columnWidth=11;source.getRange('E:E').format.columnWidth=12;
  source.getRange('F:F').format.columnWidth=40;source.getRange('F6:F475').format.wrapText=true;
  source.getRange('G:G').format.columnWidth=105;source.getRange('H:H').format.columnWidth=58;
  source.getRange('E6:E475').setNumberFormat('0.00');
  source.freezePanes.freezeRows(5);
  data.tfr.forEach((r,i)=>{if(r.year===2025){source.getRange(`A${i+6}:H${i+6}`).format.fill='#FFF2CC';source.getRange(`A${i+6}:H${i+6}`).format.rowHeight=48;}});
  const sheet=wb.worksheets.add('TFR merged');sheet.showGridLines=false;sheet.tabColor='#233F5D';
  sheet.getRange('A1:AM476').format.font={name:'Arial',size:10,color:'#182C3D'};
  sheet.getRange('A1:AM476').format.rowHeight=26;
  sheet.getRange('A1').values=[['Food imports merged with prefectural TFR']];
  sheet.getRange('A1').format.font={name:'Arial',size:15,bold:true,color:'#182C3D'};
  sheet.getRange('A2').values=[['470 rows: 47 prefectures × 10 years (2016–2025). 2025 TFR is provisional.']];
  sheet.getRange('A3').values=[['Imports are Japan national totals repeated within year, not prefectural exposure. There are ten annual import observations, not 470 independent shocks.']];
  sheet.getRange('A4').values=[['Current USD, all origins. Soyabeans overlap food totals; HS230400 oilcake is excluded. n.a. means no returned import record.']];
  sheet.getRange('A2:A4').format.font={name:'Arial',size:10,italic:true,color:'#526575'};
  const headers=['Region code','Prefecture','Japanese name','Year','Prefectural TFR','TFR release status','Import geography','Published food total (USD)','Mapped food total (USD)','Whole soyabeans (USD)','Other mapped food (USD)',
    ...data.soy_codes.map(([code,name])=>`${name} | HS${code} (USD)`),
    ...data.group_codes.map(([code,name])=>`${name} | HS${code} (USD)`)];
  sheet.getRange('A6:AM6').values=[headers];
  sheet.getRange('A6:AM6').format={fill:'#233F5D',font:{name:'Arial',size:10,bold:true,color:'#FFFFFF'},wrapText:true,rowHeight:62,verticalAlignment:'center'};
  function letter(n){let s='';while(n){n--;s=String.fromCharCode(65+n%26)+s;n=Math.floor(n/26);}return s;}
  for(let i=0;i<data.tfr.length;i++){
    const tfr=data.tfr[i],j=tfr.year-2016,row=i+7,src=i+6,annualCol=letter(j+4),soyCol=letter(j+5);
    const formulas=['A','B','C','D','E','F'].map(col=>`='Prefecture TFR'!${col}${src}`);
    sheet.getRange(`A${row}:F${row}`).formulas=[formulas];
    sheet.getRange(`G${row}`).values=[['Japan national; shared within year; not prefectural exposure']];
    sheet.getRange(`H${row}:AM${row}`).formulas=[[
      `='Annual groups'!${annualCol}29`,`='Annual groups'!${annualCol}28`,
      `=SUM(L${row}:M${row})`,`=I${row}-J${row}`,
      ...data.soy_codes.map(([, ,r])=>`=Soyabeans!${soyCol}${r}`),
      ...data.group_codes.map(([, ,r])=>`='Annual groups'!${annualCol}${r}`)]];
    if(i%2===1)sheet.getRange(`A${row}:AM${row}`).format.fill='#EAF0F5';
    if(tfr.year===2025)sheet.getRange(`A${row}:G${row}`).format.fill='#FFF2CC';
  }
  sheet.getRange('A:A').format.columnWidth=14;sheet.getRange('B:C').format.columnWidth=21;
  sheet.getRange('D:D').format.columnWidth=11;sheet.getRange('E:E').format.columnWidth=15;
  sheet.getRange('F:F').format.columnWidth=85;sheet.getRange('G:G').format.columnWidth=75;
  sheet.getRange('F7:G476').format.wrapText=true;sheet.getRange('A7:AM476').format.rowHeight=28;
  sheet.getRange('A7:AM476').format.verticalAlignment='center';
  sheet.getRange('H:AM').format.columnWidth=25;
  sheet.getRange('D7:D476').setNumberFormat('0');sheet.getRange('E7:E476').setNumberFormat('0.00');
  sheet.getRange('H7:AM476').setNumberFormat('#,##0');
  sheet.freezePanes.freezeRows(6);sheet.freezePanes.freezeColumns(4);
  wb.recalculate();
  console.log((await wb.inspect({kind:'table',range:'TFR merged!A6:H16',include:'values,formulas',tableMaxRows:11,tableMaxCols:8,maxChars:2600})).ndjson);
  console.log((await wb.inspect({kind:'match',searchTerm:'#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A|#NUM!|#NULL!',options:{useRegex:true,maxResults:20},maxChars:1800})).ndjson);
  await fs.writeFile(`${outputDir}/merged_values.json`,JSON.stringify(sheet.getRange('A7:AM476').values));
  const xlsx=await SpreadsheetFile.exportXlsx(wb);await xlsx.save(`${outputDir}/imported_food_names_with_tfr.xlsx`);
  for(const [name,range,file] of [['TFR merged','A1:H17','merged'],['TFR merged','I6:R16','soy_merged'],['TFR merged','S6:Y16','groups_merged'],['Prefecture TFR','A1:F16','tfr_source']]){
    const preview=await wb.render({sheetName:name,range,scale:1.5,format:'png'});
    await fs.writeFile(`${outputDir}/${file}.png`,new Uint8Array(await preview.arrayBuffer()));
  }
  console.log('Exported merged workbook.');
}
