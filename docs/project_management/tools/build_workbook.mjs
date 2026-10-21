// Run with @oai/artifact-tool available via NODE_PATH or adjacent node_modules.
// Source: ../plan_data.json. No production dependencies or code are modified.
import fs from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {Workbook, SpreadsheetFile} from '@oai/artifact-tool';
const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
const data=JSON.parse(await fs.readFile(path.join(root,'plan_data.json'),'utf8'));
const tasks=[...data.tasks].sort((a,b)=>a.id.localeCompare(b.id));
const resources=Object.entries(data.resources);
const wb=Workbook.create();
const names=['RESUMEN','EDT Y TAREAS','CARTA GANTT','RECURSOS','PRESUPUESTO','RIESGOS','HITOS Y CONTROL'];
const sheets=Object.fromEntries(names.map(n=>[n,wb.worksheets.add(n)]));
const navy='#17324D', blue='#245B86', pale='#EDF3F8', amber='#FFF2CC', red='#F6D6D8', green='#D9EBDD';
const last=tasks.length+5, byId=Object.fromEntries(tasks.map((t,i)=>[t.id,i+6]));
const col=n=>{let s='';for(n++;n;n=Math.floor((n-1)/26))s=String.fromCharCode(65+(n-1)%26)+s;return s;};
const put=(s,cell,value)=>s.getRange(cell).values=[[value]];
const formula=(s,cell,value)=>s.getRange(cell).formulas=[[value]];
function base(s,title,end='L',rows=60){
 s.showGridLines=false;s.tabColor=navy;
 const r=s.getRange(`A1:${end}${rows}`);r.format.font.name='Arial';r.format.font.size=10;r.format.verticalAlignment='center';r.format.columnWidth=16;r.format.rowHeight=24;
 put(s,'A1',title);s.getRange('A1').format.font.size=16;s.getRange('A1').format.font.bold=true;
 s.getRange('A1').format.font.color=navy;
}
function header(s,row,labels){const r=s.getRange(`A${row}:${col(labels.length-1)}${row}`);r.values=[labels];r.format.fill=navy;r.format.font.color='#FFFFFF';r.format.font.bold=true;r.format.wrapText=true;r.format.rowHeight=42;}
function input(s,range){s.getRange(range).format.fill=amber;s.getRange(range).format.font.color='#174DA0';}
function body(s,start,end,cols){s.getRange(`A${start}:${col(cols-1)}${end}`).format.wrapText=true;for(let r=start;r<=end;r++)if(r%2===0)s.getRange(`A${r}:${col(cols-1)}${r}`).format.fill=pale;}
const S=sheets.RESUMEN;
base(S,'ADVENTURE CAPITAL · Plan operacional de ocho meses','L',70);
put(S,'A3','Inicio contractual (ejemplo editable)');put(S,'D3',new Date(data.start_date+'T00:00:00Z'));input(S,'D3');S.getRange('D3').setNumberFormat('dd/mm/yyyy');
put(S,'A4','Meses de horizonte');put(S,'D4',data.months);input(S,'D4');
put(S,'A5','Fin contractual');formula(S,'D5','=EDATE(D3,D4)-1');S.getRange('D5').setNumberFormat('dd/mm/yyyy');
put(S,'A6','Fin previsto');formula(S,'D6',`=WORKDAY(D3-1,MAX('EDT Y TAREAS'!AN6:AN${last}),J6:J25)`);S.getRange('D6').setNumberFormat('dd/mm/yyyy');
put(S,'A7','Reserva restante (días hábiles)');formula(S,'D7','=NETWORKDAYS(D3,D5,J6:J25)-MAX(\'EDT Y TAREAS\'!AN6:AN'+last+')');
put(S,'A8','Esfuerzo de tareas (h-persona)');formula(S,'D8',`=SUM('EDT Y TAREAS'!L6:L${last})`);
put(S,'A9','Esfuerzo total, coordinación incluida');formula(S,'D9',"=SUM('RECURSOS'!D6:D12)");
put(S,'A10','Presupuesto caja referencial (CLP)');formula(S,'D10',"='PRESUPUESTO'!F19");S.getRange('D10').setNumberFormat('"$"#,##0');
put(S,'F3','Amarillo: editable · Azul: enlace/cálculo');
put(S,'F4','CPM: días hábiles, lunes–viernes; feriados editables en J6:J25.');
put(S,'F5','Fecha inicial de ejemplo; no equivale a adjudicación ni inicio aprobado.');
put(S,'J4','Feriados / días no laborables');input(S,'J6:J25');S.getRange('J6:J25').setNumberFormat('dd/mm/yyyy');
S.getRange('A3:C10').format.columnWidth=17;S.getRange('D3:D10').format.columnWidth=20;S.getRange('F3:F5').format.columnWidth=68;S.getRange('J4:J25').format.columnWidth=25;
header(S,13,['Etapa','Objetivo','Entregable principal','Fin previsto','Responsable']);
const phases=[['Encuadre','Aprobar producto y proveedor','Contrato, requisitos y fronteras','Alejandro + Alonso'],['Validación científica','Corregir y delimitar metodología','Motor y métricas verificables','Alonso'],['Producto SaaS','Empaquetar motor con acceso seguro','Recorrido multiusuario y operación','Empresa'],['Piloto y calidad','Verificar uso, exactitud y compra','Tres organizaciones y dos rondas','Empresa + Alonso'],['Entrega comercial','Lanzar y transferir operación','Versión aceptada y oferta comercial','Alejandro']];
phases.forEach((p,i)=>{const r=14+i;put(S,`A${r}`,`${i+1}. ${p[0]}`);put(S,`B${r}`,p[1]);put(S,`C${r}`,p[2]);formula(S,`D${r}`,`=MAX(${tasks.filter(t=>t.phase===i+1).map(t=>`'EDT Y TAREAS'!O${byId[t.id]}`).join(',')})`);put(S,`E${r}`,p[3]);});
S.getRange('D14:D18').setNumberFormat('dd/mm/yyyy');body(S,14,18,5);S.getRange('A14:E18').format.rowHeight=60;
for(const [c,w] of [['A',30],['B',34],['C',40],['D',20],['E',28]]) S.getRange(`${c}13:${c}18`).format.columnWidth=w;
const notes=[
 'Producto: SaaS acotado de planificación, escenarios y reportes para startups/consultores.',
 'Alonso: ciencia y aceptación técnica. Empresa: SaaS, UI/UX, perfiles, QA e infraestructura.',
 'Edite duración, horas por recurso, avance y fecha; CPM, Gantt, cargas y presupuesto se recalculan.',
 'Predecesoras: guardar Excel → tools/refresh_from_xlsx.py → regenerar. Nuevas tareas se agregan al JSON.',
 'Las predecesoras J/K muestran la red vigente. No ordene físicamente EDT; use filtros.',
 'T=técnica, V=validación, C=contrato, R=recurso. R representa un conflicto real de capacidad.',
 'Holgura respecto del fin más temprano de la red nivelada; reserva contractual aparece arriba.',
 'La nivelación es heurística y se recalcula con script; Excel alerta sobrecargas tras editar.',
 'Duraciones O/P/C son rangos de planificación, no intervalos estadísticos ni garantía del plazo.',
 'Alonso reserva 40 h/semana: 36 para tareas y 2 coordinación; el resto para interrupciones.',
 'Pilotos de 5 días requieren 3 organizaciones preagendadas; sin ese compromiso consumirán reserva.',
 'M4 se investiga sin bloquear el MVP determinista; publicación requiere aprobación científica.',
];notes.forEach((x,i)=>put(S,`A${22+i}`,x));S.getRange('A22:A33').format.columnWidth=30;

const T=sheets['EDT Y TAREAS'];base(T,'EDT · tareas, esfuerzo y red CPM','AS',last+2);
put(T,'A3','Duración y esfuerzo independientes. Editar horas por recurso en AD:AJ; L se calcula. Inicio/fin son fechas.');
put(T,'A4','J/K: enlaces FS y tipos; al cambiarlos ejecutar actualización. Fechas/holguras se basan en la red vigente.');
header(T,5,['ID','Código EDT','Etapa','Módulo','Tarea','Descripción','Entregable','Responsable','Colaborador','Predecesoras','Tipo de dependencia','Esfuerzo estimado (horas)','Duración (días hábiles)','Inicio temprano','Fin temprano','Inicio tardío','Fin tardío','Holgura (días)','Ruta crítica','Semana inicio','Semana término','Estado','Avance','Criterio de aceptación','Prioridad','Días-persona (8 h)','Optimista (días)','Conservadora (días)','Recursos necesarios','AP h','AM h','BE h','FE h','UX h','QA h','OP h','ES día 0','EF exclusivo','LS día 0','LF exclusivo','Inicio red vigente','Fin red vigente','Diferencia red','Reserva']);
body(T,6,last,44);
for(const [i,t] of tasks.entries()){
 const r=i+6, owner=data.resources[({'T38':'AM','T46':'AM'})[t.id]||t.owner].name;
 const vals=[t.id,t.wbs,phases[t.phase-1][0],t.module,t.title,t.title+'; revisar evidencia y registrar decisión.',t.deliverable,owner,Object.keys(t.effort).filter(x=>x!==t.owner).join(', '),t.dependencies.map(x=>x.id).join(', '),t.dependencies.map(x=>x.type).join(', '),null,t.duration,null,null,null,null,null,null,null,null,t.status,t.progress,t.acceptance,t.priority,null,t.optimistic,t.conservative,'Repo, staging y casos sintéticos',...resources.map(([k])=>t.effort[k]||0),null,null,null,null,t.es,t.ef,null,null];
 T.getRange(`A${r}:AR${r}`).values=[vals];
 formula(T,`L${r}`,`=SUM(AD${r}:AJ${r})`);formula(T,`Z${r}`,`=L${r}/8`);
 formula(T,`AK${r}`,t.dependencies.length?`=MAX(${t.dependencies.map(d=>`AL${byId[d.id]}`).join(',')})`:'=0');
 formula(T,`AL${r}`,`=AK${r}+M${r}`);
 const succ=tasks.filter(x=>x.dependencies.some(d=>d.id===t.id));
 formula(T,`AN${r}`,succ.length?`=MIN(${succ.map(x=>`AM${byId[x.id]}`).join(',')})`:`=MAX(AL$6:AL$${last})`);
 formula(T,`AM${r}`,`=AN${r}-M${r}`);
 for(const [c,d,offset] of [['N','AK',1],['O','AL',0],['P','AM',1],['Q','AN',0]])formula(T,`${c}${r}`,`=WORKDAY('RESUMEN'!$D$3-1,${d}${r}+${offset},'RESUMEN'!$J$6:$J$25)`);
 formula(T,`R${r}`,`=AM${r}-AK${r}`);formula(T,`S${r}`,`=IF(R${r}=0,"Sí","No")`);
 formula(T,`T${r}`,`=INT((N${r}-'RESUMEN'!$D$3)/7)+1`);formula(T,`U${r}`,`=INT((O${r}-'RESUMEN'!$D$3)/7)+1`);
 formula(T,`AQ${r}`,`=AK${r}-AO${r}`);formula(T,`AR${r}`,`='RESUMEN'!$D$7`);
}
T.getRange(`N6:Q${last}`).setNumberFormat('dd/mm/yyyy');T.getRange(`W6:W${last}`).setNumberFormat('0%');T.getRange(`Z6:Z${last}`).setNumberFormat('0.0');
for(const c of ['J','K','M','V','W','AA','AB','AD','AE','AF','AG','AH','AI','AJ'])input(T,`${c}6:${c}${last}`);
for(const [c,w] of [['A',9],['B',11],['C',24],['D',20],['E',48],['F',58],['G',45],['H',28],['I',20],['J',28],['K',18],['X',72],['AC',34]])T.getRange(`${c}5:${c}${last}`).format.columnWidth=w;
T.getRange(`A6:AR${last}`).format.rowHeight=64;T.freezePanes.freezeRows(5);T.freezePanes.freezeColumns(2);
T.getRange(`V6:V${last}`).dataValidation={rule:{type:'list',values:['No iniciada','En curso','Bloqueada','Terminada']}};
T.getRange(`M6:M${last}`).dataValidation={rule:{type:'whole',operator:'between',formula1:1,formula2:80}};
T.getRange(`S6:S${last}`).conditionalFormats.add('containsText',{text:'Sí',format:{fill:red,font:{bold:true}}});
T.tables.add(`A5:AR${last}`,true,'TaskRegister');

const G=sheets['CARTA GANTT'];base(G,'CARTA GANTT · semanas relativas al contrato','AM',last+14);
put(G,'A3','Rojo: ruta crítica · Azul: otras tareas · Verde: hito · Reserva posterior al cierre hasta ocho meses.');
header(G,5,['ID','Etapa / tarea','Responsable','Inicio','Fin','Crítica',...Array.from({length:35},(_,i)=>`S${i+1}`)]);
G.getRange('A5').format.columnWidth=9;G.getRange('B5').format.columnWidth=55;G.getRange('C5').format.columnWidth=26;G.getRange('D5:F5').format.columnWidth=12;G.getRange('G5:AO5').format.columnWidth=5;
tasks.forEach((t,i)=>{const r=i+6,tr=byId[t.id];put(G,`A${r}`,t.id);put(G,`B${r}`,`${t.wbs} · ${t.title}`);put(G,`C${r}`,data.resources[t.owner].name);for(const [dest,src] of [['D','T'],['E','U'],['F','S']])formula(G,`${dest}${r}`,`='EDT Y TAREAS'!${src}${tr}`);
 for(let w=1;w<=35;w++)formula(G,`${col(w+5)}${r}`,`=IF(AND(${w}>=$D${r},${w}<=$E${r}),IF($F${r}="Sí",2,1),0)`);
});G.getRange(`G6:AO${last}`).setNumberFormat(';;;');
G.getRange(`G6:AO${last}`).conditionalFormats.add('cellIs',{operator:'equal',formula:2,format:{fill:'#B84B54'}});
G.getRange(`G6:AO${last}`).conditionalFormats.add('cellIs',{operator:'equal',formula:1,format:{fill:'#608CAE'}});
G.getRange(`B6:C${last}`).format.wrapText=true;G.getRange(`A6:AO${last}`).format.rowHeight=36;G.freezePanes.freezeRows(5);G.freezePanes.freezeColumns(2);

const R=sheets.RECURSOS;base(R,'RECURSOS · disponibilidad, carga y coordinación','AO',305);
put(R,'A3','Capacidades de tarea reservadas; coordinación adicional AP 2 h/sem, AM 1 h/sem y BE 2 h/sem (S4–32).');
header(R,5,['Recurso','Rol','Capacidad tareas h/sem','Horas totales','FTE medio (40 h)','Meses equivalentes','Responsabilidades','Tarifa CLP/h','Costo económico','Horas tareas','Horas coordinación','Pico semanal tareas','Estado']);
resources.forEach(([k,v],i)=>{let r=6+i;put(R,`A${r}`,v.name);put(R,`B${r}`,v.role);put(R,`C${r}`,v.capacity);formula(R,`J${r}`,`=SUM('EDT Y TAREAS'!${col(29+i)}6:${col(29+i)}${last})`);
 put(R,`K${r}`,k==='AP'?70:k==='AM'?35:k==='BE'?58:0);formula(R,`D${r}`,`=J${r}+K${r}`);formula(R,`E${r}`,`=D${r}/(40*35)`);formula(R,`F${r}`,`=D${r}/(40*52/12)`);put(R,`G${r}`,v.role);put(R,`H${r}`,v.rate);
 formula(R,`I${r}`,k==='AP'?"='PRESUPUESTO'!F6":`=D${r}*H${r}`);formula(R,`L${r}`,`=MAX(G${18+i}:AO${18+i})`);formula(R,`M${r}`,`=IF(MAX('EDT Y TAREAS'!AL6:AL${last})>260,"Ampliar control diario",IF(MAX(${col(i+1)}40:${col(i+1)}299)>C${r}/5,"Sobrecarga","Dentro de capacidad"))`);
});input(R,'C6:C12');input(R,'H6:H12');R.getRange('E6:E12').setNumberFormat('0%');R.getRange('F6:F12').setNumberFormat('0.0');R.getRange('H6:I12').setNumberFormat('"$"#,##0');
header(R,17,['Carga semanal','Rol','Capacidad','Pico','Control','',...Array.from({length:35},(_,i)=>`S${i+1}`)]);
resources.forEach(([k,v],i)=>{const r=18+i;put(R,`A${r}`,v.name);formula(R,`C${r}`,`=C${i+6}`);formula(R,`D${r}`,`=MAX(G${r}:AO${r})`);formula(R,`E${r}`,`=M${i+6}`);
 for(let w=0;w<35;w++)formula(R,`${col(w+6)}${r}`,`=SUMIFS(${col(i+1)}$40:${col(i+1)}$299,$I$40:$I$299,">="&('RESUMEN'!$D$3+${w*7}),$I$40:$I$299,"<"&('RESUMEN'!$D$3+${(w+1)*7}))`);
 R.getRange(`G${r}:AO${r}`).conditionalFormats.addCustom(`G${r}>$C${r}`,{fill:red});});
put(R,'A27','Hardware: mantener MacBook M1; sustituir sólo por memoria/SSD/batería insuficiente medidos. Sin GPU local.');
put(R,'A28','Licencias: una principal entre ChatGPT/Claude; segunda sólo si aporta valor medido. Gemini gratuito si basta.');
put(R,'A29','Infraestructura: staging + producción gestionada, PostgreSQL, objetos privados y workers CPU; sin Kubernetes inicial.');
put(R,'A30','Horas uniformes por tarea. El detalle diario detecta sobrecargas que el promedio semanal puede ocultar.');
put(R,'A31','Para sumar tareas o cambiar enlaces, regenerar y volver a nivelar. No resolver alertas inflando disponibilidad ficticia.');
put(R,'N5','Mes inicio tareas');put(R,'O5','Mes término tareas');
resources.forEach(([k],i)=>{const rr=i+6,active=tasks.filter(t=>t.effort[k]);
 const min=`MIN(${active.map(t=>`'EDT Y TAREAS'!N${byId[t.id]}`).join(',')})`;
 const max=`MAX(${active.map(t=>`'EDT Y TAREAS'!O${byId[t.id]}`).join(',')})`;
 formula(R,`N${rr}`,`=(YEAR(${min})-YEAR('RESUMEN'!$D$3))*12+MONTH(${min})-MONTH('RESUMEN'!$D$3)+1`);
 formula(R,`O${rr}`,`=(YEAR(${max})-YEAR('RESUMEN'!$D$3))*12+MONTH(${max})-MONTH('RESUMEN'!$D$3)+1`);
});R.getRange('N5:O5').format.fill=navy;R.getRange('N5:O5').format.font.color='#FFFFFF';R.getRange('N5:O12').format.columnWidth=20;R.getRange('N5:O5').format.wrapText=true;
header(R,39,['Día hábil',...resources.map(([k])=>k),'Fecha']);
for(let d=0;d<260;d++){let r=40+d;put(R,`A${r}`,d+1);formula(R,`I${r}`,`=WORKDAY('RESUMEN'!$D$3-1,A${r},'RESUMEN'!$J$6:$J$25)`);resources.forEach(([k],i)=>{
 const terms=tasks.filter(t=>t.effort[k]).map(t=>{const tr=byId[t.id];return `IF(AND(${d}>='EDT Y TAREAS'!AK${tr},${d}<'EDT Y TAREAS'!AL${tr}),'EDT Y TAREAS'!${col(29+i)}${tr}/'EDT Y TAREAS'!M${tr},0)`;});
 formula(R,`${col(i+1)}${r}`,'=SUM('+terms.join(',')+')');
});}
for(const [c,w] of [['A',30],['B',38],['C',18],['D',15],['G',40],['M',24]])R.getRange(`${c}5:${c}12`).format.columnWidth=w;
R.getRange('A6:M12').format.wrapText=true;R.getRange('A6:M12').format.rowHeight=60;R.getRange('G18:AO24').setNumberFormat('0.0');R.getRange('B40:H299').setNumberFormat('0.0');R.getRange('I40:I299').setNumberFormat('dd/mm/yyyy');R.freezePanes.freezeRows(5);

const B=sheets.PRESUPUESTO;base(B,'PRESUPUESTO · referencia exploratoria, no cotización','S',50);
put(B,'A3','CLP. Prioridad secundaria por instrucción del usuario. Impuestos/cargas se confirman al contratar. No adjudicación CORFO.');
header(B,5,['Categoría','Concepto','Cantidad','Costo unitario CLP','Mes inicio','Costo total CLP','Justificación','Prioridad','Alternativa','Elegibilidad CORFO por confirmar','Meses distribución',...Array.from({length:8},(_,i)=>`Mes ${i+1}`)]);
const budget=[
 ['Personal','Alonso · ocho meses',8,1400000,1,'Ciencia, integración y supervisión','P0','Dedicación pactada; 6 meses requieren relevo','Revisar vínculo y tope socios',8],
 ['Empresa','Backend + arquitectura + coordinación',null,25000,1,'Contrato API, datos, trabajos y revisión','P0','Monolito Python con UI sencilla','Por confirmar por actividad',8],
 ['Empresa','Frontend',null,25000,2,'Recorrido de usuario y perfiles','P0','UI servidor; React sólo si justificado','Por confirmar',6],
 ['Empresa','UI/UX',null,25000,1,'Investigación, pruebas y diseño','P0','Alcance acotado a recorrido principal','Por confirmar',8],
 ['Empresa','QA independiente',null,25000,2,'Pruebas de producto y aceptación','P0','Automatización focal y revisión externa','Por confirmar',7],
 ['Empresa','Operación y seguridad',null,25000,1,'Entornos, respaldos y entrega','P0','Servicios gestionados','Por confirmar',8],
 ['Software','Licencias de desarrollo',8,40000,1,'Una principal + segunda opcional','P1','Una licencia o niveles gratuitos','Por confirmar',8],
 ['Infraestructura','Hosting, DB, storage y observabilidad',8,200000,1,'Staging y piloto con límites','P0','Escalar tras medir carga','Por confirmar',8],
 ['Validación','Legal y seguridad complementaria',1,1000000,5,'Revisión externa acotada','P0','Encargo por entregable','Por confirmar',1],
 ['Operación','Dominio y correo',1,100000,1,'Identidad y operación comercial','P1','Plan básico','Por confirmar',1],
 ['Hardware','Nuevo portátil / equipo SSH',0,1500000,4,'No compra base; decisión por medición','P2','Mantener M1 y cloud puntual','No incluir hasta justificar',1],
 ['Contingencia','Reserva explícita 15% base',0.15,null,1,'Incertidumbre, impuestos y retrabajo por confirmar','P0','Liberar por aprobación de Alejandro','No presumir elegible',8],
];budget.forEach((x,i)=>{const r=6+i;let [cat,concept,q,u,m,why,p,alt,elig,months]=x;B.getRange(`A${r}:K${r}`).values=[[cat,concept,q,u,m,null,why,p,alt,elig,months]];
 if(i>=1&&i<=5){const rr={1:8,2:9,3:10,4:11,5:12}[i];formula(B,`C${r}`,`='RECURSOS'!D${rr}`);formula(B,`D${r}`,`='RECURSOS'!H${rr}`);}
 if(i===11)formula(B,`D${r}`,'=SUM(F6:F16)');formula(B,`F${r}`,`=C${r}*D${r}`);
 for(let mth=1;mth<=8;mth++)formula(B,`${col(mth+10)}${r}`,`=IF(AND(${mth}>=E${r},${mth}<E${r}+K${r}),F${r}/K${r},0)`);
});
put(B,'A19','Total caja con reserva');formula(B,'F19','=SUM(F6:F17)');for(let m=0;m<8;m++)formula(B,`${col(m+11)}19`,`=SUM(${col(m+11)}6:${col(m+11)}17)`);
put(B,'A21','Alejandro: aporte económico de tiempo');formula(B,'F21',"='RECURSOS'!I7");put(B,'A22','Total económico (caja + tiempo director)');formula(B,'F22','=F19+F21');
put(B,'A24','Distribución mensual lineal editable: provisión de caja, no calendario contractual de facturación.');
put(B,'A25','Empresa: tarifa supuesta CLP 25.000/h; banda 18.000–35.000/h. Reemplazar por propuesta por hitos.');
put(B,'A26','No se presupuesta API de IA obligatoria ni compra de computador. CORFO financiable queda sin determinar.');
put(B,'A27','Fuentes: supuestos de planificación; remuneración entregada por usuario; ver Plan Director para restricciones CORFO.');
input(B,'C6:E17');input(B,'K6:K17');B.getRange('D6:D17').setNumberFormat('"$"#,##0');B.getRange('F6:F22').setNumberFormat('"$"#,##0');B.getRange('L6:S19').setNumberFormat('"$"#,##0');B.getRange('C17').setNumberFormat('0%');
body(B,6,17,19);B.getRange('A6:K17').format.rowHeight=60;for(const [c,w] of [['A',20],['B',40],['G',45],['I',42],['J',35]]) B.getRange(`${c}5:${c}17`).format.columnWidth=w;B.freezePanes.freezeRows(5);

const riskRows=[
 ['R01','Método entrega cifras inconsistentes',4,5,'T09–T15: casos manuales, contrato de unidades, revisión científica','Alonso','T09,T10,T12,T15','No publicar métricas sin conciliar'],
 ['R02','Fuga de datos entre organizaciones',3,5,'Aislamiento por objeto, render seguro, revisión independiente','Empresa','T20,T28,T34,T37','Bloquea piloto real'],
 ['R03','Proveedor no reserva perfiles o llega tarde',3,4,'Contrato temprano por hitos y nombres; acceso al repo desde inicio','Alejandro','T03,T04','Reducir alcance a piloto asistido'],
 ['R04','Alonso absorbe tareas SaaS y desplaza ciencia',4,4,'RACI; 2h/sem coordinación y revisiones con límites','Alonso','T06,T23,T44','Escalar capacidad del proveedor'],
 ['R05','Usuarios no disponibles para rondas de cinco días',3,4,'Agendar tres organizaciones al contratar; suplentes','Alejandro','T39,T41','Consumir reserva o reducir cohorte'],
 ['R06','Supuestos de mercado no sustentados',4,4,'Separar regla metodológica de benchmark; registrar fuente y fecha','Alonso','T11,T14','Restringir claims comerciales'],
 ['R07','Plazo conservador excede ocho meses',4,4,'Reestimar en S6; diferir M4 y comparación avanzada','Alejandro','T07,T38,T46','Priorizar MVP determinista'],
 ['R08','Financiamiento o elegibilidad no confirmados',4,4,'Validar convocatoria y caja antes de contratar','Alejandro','T04','No comprometer gasto suponiendo subsidio'],
 ['R09','Dependencia del proveedor',3,4,'Cuentas propias, código, infraestructura declarativa y ensayo de salida','Empresa','T44','Retener pago de entrega hasta transferencia'],
 ['R10','Modelo lento bajo concurrencia',3,4,'Límites H/S/escenarios, worker CPU y cancelación; benchmark','Empresa','T22,T35','Desactivar M4 público y reducir concurrencia'],
 ['R11','No se obtiene primera venta',3,4,'Entrevistas tempranas, propuesta desde piloto; medir disposición a pagar','Alejandro','T33,T42','Revisar segmento/oferta antes de ampliar'],
 ['R12','Tratamiento de datos sin base adecuada',3,5,'Inventario, minimización, autorización y revisión legal','Alejandro','T32,T37','Usar sólo datos sintéticos hasta cierre'],
];
const K=sheets.RIESGOS;base(K,'RIESGOS · decisiones y contingencias','I',24);put(K,'A3','Escala 1–5: probabilidad e impacto cualitativos; puntuación = P × I. No probabilidades estadísticas.');
header(K,5,['ID','Riesgo','Probabilidad','Impacto','Mitigación','Responsable','Actividad afectada','Contingencia / disparador','Puntuación']);
riskRows.forEach((v,i)=>{const r=i+6;K.getRange(`A${r}:H${r}`).values=[v];formula(K,`I${r}`,`=C${r}*D${r}`);});body(K,6,17,9);K.getRange('A6:I17').format.rowHeight=70;for(const [c,w] of [['A',8],['B',42],['E',65],['F',22],['G',24],['H',44]])K.getRange(`${c}5:${c}17`).format.columnWidth=w;input(K,'C6:D17');K.getRange('I6:I17').conditionalFormats.add('cellIs',{operator:'greaterThanOrEqual',formula:16,format:{fill:red}});K.freezePanes.freezeRows(5);

const H=sheets['HITOS Y CONTROL'];base(H,'HITOS Y CONTROL · aceptación y decisiones','H',55);
header(H,5,['Hito','Fecha objetivo','Entregable','Responsable','Criterio de aceptación','Estado','Semana','Tarea']);
const milestones=[['Contrato empresa','T04'],['Alcance y UX aprobados','T07'],['Motor aceptado','T15'],['Recorrido SaaS integrado','T27'],['Autorización piloto','T38'],['Piloto repetido','T41'],['Primera oferta negociada','T42'],['Transferencia','T44'],['Lanzamiento aprobado','T46'],['Operación acompañada','T47']];
milestones.forEach(([name,id],i)=>{const t=tasks.find(t=>t.id===id),r=i+6,tr=byId[id];put(H,`A${r}`,name);formula(H,`B${r}`,`='EDT Y TAREAS'!O${tr}`);put(H,`C${r}`,t.deliverable);put(H,`D${r}`,data.resources[t.owner].name);put(H,`E${r}`,t.acceptance);put(H,`F${r}`,'Pendiente');formula(H,`G${r}`,`='EDT Y TAREAS'!U${tr}`);put(H,`H${r}`,id);
 const gr=last+3+i;put(G,`A${gr}`,'H'+(i+1));put(G,`B${gr}`,name);formula(G,`D${gr}`,`='HITOS Y CONTROL'!G${r}`);for(let w=1;w<=35;w++)formula(G,`${col(w+5)}${gr}`,`=IF(${w}=$D${gr},3,0)`);
});H.getRange('B6:B15').setNumberFormat('dd/mm/yyyy');body(H,6,15,8);H.getRange('A6:H15').format.rowHeight=72;for(const [c,w] of [['A',34],['B',18],['C',45],['D',28],['E',80]])H.getRange(`${c}5:${c}15`).format.columnWidth=w;input(H,'F6:F15');
put(H,'D10','Alejandro Maureira');put(H,'D14','Alejandro Maureira');
G.getRange(`G${last+3}:AO${last+12}`).setNumberFormat(';;;');G.getRange(`G${last+3}:AO${last+12}`).conditionalFormats.add('cellIs',{operator:'equal',formula:3,format:{fill:'#2C7851'}});
put(H,'A19','Control semanal');put(H,'A20','Lunes: seleccionar tareas activas por semana, confirmar capacidad y decisiones pendientes.');put(H,'A21','Diario: actualizar estado/avance y registrar bloqueo; descomponer tarea activa en acciones de 0,5–2 días.');put(H,'A22','Viernes: demo verificable, aceptación del responsable y actualización de riesgo/plazo.');put(H,'A23','Cada dos semanas: Alejandro decide alcance; Alonso acepta ciencia; empresa demuestra producto y QA.');

for(const [name,overrides] of Object.entries(data.workbook_overrides||{}))for(const [cell,value] of Object.entries(overrides))put(sheets[name],cell,value);
// Recalculation, independent CPM agreement, input mutation, and bounded errors.
wb.recalculate();
const scalar=(s,c)=>s.getRange(c).values[0][0];
for(const t of tasks){const r=byId[t.id];if(scalar(T,`AK${r}`)!==t.es||scalar(T,`AL${r}`)!==t.ef||scalar(T,`R${r}`)!==t.float)throw Error('CPM mismatch '+t.id+' '+JSON.stringify(T.getRange(`AK${r}:AN${r}`).values));}
const old=scalar(T,'M6'),oldEnd=scalar(T,`AL${byId.T47}`);put(T,'M6',old+1);wb.recalculate();const newEnd=scalar(T,`AL${byId.T47}`);if(newEnd!==oldEnd+1)throw Error('Duration edit did not propagate');put(T,'M6',old);wb.recalculate();
const oldDate=scalar(S,'D3'),oldFinish=scalar(S,'D6');put(S,'D3',new Date('2026-11-09T00:00:00Z'));wb.recalculate();const shiftedFinish=scalar(S,'D6');if(shiftedFinish===oldFinish)throw Error('Start date did not propagate');put(S,'D3',oldDate);wb.recalculate();
const oldCap=scalar(R,'C6');put(R,'C6',1);wb.recalculate();if(scalar(R,'M6')!=='Sobrecarga')throw Error('Capacity flag not reactive');put(R,'C6',oldCap);wb.recalculate();
const oldRate=scalar(R,'H8'),oldBudget=scalar(B,'F19');put(R,'H8',oldRate+1000);wb.recalculate();if(scalar(B,'F19')<=oldBudget)throw Error('Rate edit not reactive');put(R,'H8',oldRate);wb.recalculate();
const errors=await wb.inspect({kind:'match',searchTerm:'#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A|#NUM!|#NULL!|#SPILL!|#CALC!',options:{useRegex:true,maxResults:50},summary:'Formula validation'});
await fs.writeFile(path.join(root,'evidence','workbook_errors.ndjson'),errors.ndjson);
const summary=await wb.inspect({kind:'table',range:'RESUMEN!A3:D10',include:'values,formulas',tableMaxRows:8,tableMaxCols:4});
await fs.writeFile(path.join(root,'evidence','workbook_summary.ndjson'),summary.ndjson);
await fs.mkdir(path.join(root,'evidence','previews'),{recursive:true});
const ranges=['A1:E18','A5:E10','A5:T18','A5:F12','A5:F12','A5:F10','A5:E10'];
for(let i=0;i<names.length;i++){
 const preview=await wb.render({sheetName:names[i],range:ranges[i],scale:1.3,format:'png'});
 await fs.writeFile(path.join(root,'evidence','previews',`${i+1}.png`),new Uint8Array(await preview.arrayBuffer()));
}
await (await SpreadsheetFile.exportXlsx(wb)).save(path.join(root,'03_PLAN_OPERACIONAL.xlsx'));
console.log(JSON.stringify({tasks:tasks.length,totalEffort:scalar(S,'D9'),budget:scalar(B,'F19'),economic:scalar(B,'F22'),deadlineReserve:scalar(S,'D7'),durationMutation:{oldEnd,newEnd},errors:errors.ndjson}));
