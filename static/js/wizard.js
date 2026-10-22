(() => {
  const root = document.getElementById('wizard');
  if (!root) return;
  const id = root.dataset.programId;
  const readOnly = root.dataset.readOnly === 'true';
  const csrf = document.querySelector('[name=csrfmiddlewaretoken]')?.value || '';
  const catalog = JSON.parse(document.getElementById('sicap-catalog').textContent);
  let payload = JSON.parse(document.getElementById('sicap-payload').textContent || '{}');
  let step = Number(root.dataset.startStep || 1);
  const panel = n => root.querySelector(`[data-screen="${n}"]`);
  const value = key => root.querySelector(`[data-key="${key}"]`);
  const positions = ['Titular','Asociado/a','Adjunto/a','Jefe/a de trabajos prácticos','Ayudante de primera','Ayudante de segunda','Adscripto/a','Otro'];
  const degreeChoices = feminine => [feminine ? 'Abogada' : 'Abogado','Especialista','Magíster',feminine ? 'Licenciada' : 'Licenciado',feminine ? 'Doctora' : 'Doctor',feminine ? 'Escribana' : 'Escribano',feminine ? 'Técnica' : 'Técnico','Otro'];
  const esc = s => String(s ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const subjectSelect = document.getElementById('subjectSelect');

  function set(key, val) {
    const el = value(key); if (!el) return;
    if (el.type === 'checkbox') el.checked = Boolean(val); else el.value = val ?? '';
  }
  function restoreScalarFields() {
    root.querySelectorAll('[data-key]').forEach(el => {
      const key = el.dataset.key;
      if (['team','assessments','consultations','subject_name'].includes(key)) return;
      if (Object.prototype.hasOwnProperty.call(payload, key)) set(key, payload[key]);
    });
  }
  function setSubjectDefaults(option, reset) {
    if (!option || !option.value) return;
    const courseYear = option.dataset.year || option.dataset.group || '';
    if (reset || !value('course_year').value) set('course_year', courseYear);
    if (reset || !value('hours').value) set('hours', option.dataset.hours || '');
    if (reset || !value('prerequisites_to_take').value) set('prerequisites_to_take', option.dataset.take || '');
    if (reset || !value('prerequisites_to_exam').value) set('prerequisites_to_exam', option.dataset.exam || '');
    if (reset || !value('shift').value) set('shift', option.dataset.shift || '');
    if (reset || !value('weekly_hours').value) set('weekly_hours', option.dataset.weekly || '');
    if (reset || !value('credits').value) set('credits', option.dataset.credits || '');
    const status = document.getElementById('catalogStatus');
    status.textContent = option.dataset.verified === 'true'
      ? 'Datos curriculares verificados en el catálogo institucional.'
      : 'Horas precargadas desde el listado compartido. Correlatividades pendientes de verificación en el Plan 2017.';
  }
  function firstName(fullName) {
    const parts = String(fullName || '').split(',');
    return (parts.length > 1 ? parts[1] : parts[0]).trim().split(/\s+/)[0].toLowerCase();
  }
  function inferredPrefix(fullName) {
    const name = firstName(fullName).normalize('NFD').replace(/[\u0300-\u036f]/g, '');
    const feminineNames = new Set(['ana','maria','carla','paula','laura','lucia','sofia','camila','valentina','julieta','florencia','daniela','gabriela','romina','silvia','patricia','elena','ines','beatriz','marta','veronica','cecilia','mariana','andrea','noelia','rocio','natalia','claudia','lorena','silvina','agustina','emilia','victoria','miriam']);
    const masculineNames = new Set(['juan','luis','carlos','jose','jorge','miguel','martin','pablo','diego','alejandro','ricardo','daniel','fernando','gustavo','sergio','eduardo','roberto','facundo','matias','nicolas','sebastian','francisco','gabriel','mariano','ignacio','esteban','ramon','hector','oscar','manuel','andres','tomas','lucas','leonardo','emilio','julian','rafael']);
    if (feminineNames.has(name)) return 'Profesora';
    if (masculineNames.has(name)) return 'Profesor';
    return /[oa]$/.test(name) ? (name.endsWith('o') ? 'Profesor' : 'Profesora') : 'Profesora';
  }
  function createTeacher(member = {}) {
    const card = document.createElement('article'); card.className = 'repeat-card teacher-card';
    card.innerHTML = `<div class="repeat-card-head"><strong>Integrante del equipo docente</strong><button type="button" class="remove-row">Quitar</button></div>
      <div class="team-grid">
       <label>Cargo<select class="teacher-position"><option value="">Seleccionar cargo</option>${positions.map(x=>`<option>${x}</option>`).join('')}</select><input class="teacher-position-other hidden" placeholder="Especificar cargo"></label>
       <label>Nombre y apellido<input class="teacher-name" autocomplete="off" placeholder="Nombre y apellido"></label>
       <label>Tratamiento<select class="teacher-prefix"><option>Profesora</option><option>Profesor</option></select><small>Sugerido por el nombre; se puede corregir.</small></label>
      </div><p class="field-note degree-label">Títulos de base · podés marcar más de uno</p><div class="title-options"></div>
      <label class="teacher-custom-label hidden">Especificar título<input class="teacher-custom" placeholder="Título de base o título adicional"></label>`;
    const name = card.querySelector('.teacher-name'), prefix = card.querySelector('.teacher-prefix'), position = card.querySelector('.teacher-position');
    name.value = member.name || '';
    position.value = positions.includes(member.position) ? member.position : (member.position ? 'Otro' : '');
    if (position.value === 'Otro') card.querySelector('.teacher-position-other').value = member.position;
    card.querySelector('.teacher-position-other').classList.toggle('hidden', position.value !== 'Otro');
    prefix.value = member.prefix || inferredPrefix(name.value);
    if (member.name) name.dataset.touched = '1';
    function renderDegrees(selected = []) {
      const options = degreeChoices(prefix.value === 'Profesora');
      card.querySelector('.title-options').innerHTML = options.map(x=>`<label class="choice-chip"><input type="checkbox" value="${x}" class="teacher-degree">${x}</label>`).join('');
      card.querySelectorAll('.teacher-degree').forEach(check => { check.checked = selected.includes(check.value); });
      card.querySelector('.teacher-custom-label').classList.toggle('hidden', !card.querySelector('.teacher-degree[value="Otro"]')?.checked);
      card.querySelectorAll('.teacher-degree').forEach(check => check.addEventListener('change', () => {
        card.querySelector('.teacher-custom-label').classList.toggle('hidden', !card.querySelector('.teacher-degree[value="Otro"]').checked);
      }));
    }
    const savedDegrees = (member.degrees || '').split(' · ').filter(Boolean);
    renderDegrees(savedDegrees.map(d => degreeChoices(prefix.value === 'Profesora').includes(d) ? d : 'Otro'));
    const customDegree = savedDegrees.find(d => !degreeChoices(prefix.value === 'Profesora').includes(d));
    if (customDegree) card.querySelector('.teacher-custom').value = customDegree;
    name.addEventListener('input', () => {
      if (!name.dataset.manualPrefix) {
        const prior = [...card.querySelectorAll('.teacher-degree:checked')].map(c=>c.value);
        const inferred = inferredPrefix(name.value);
        if (prefix.value !== inferred) { prefix.value = inferred; renderDegrees(prior); }
      }
    });
    prefix.addEventListener('change', () => {
      name.dataset.manualPrefix = '1';
      const prior = [...card.querySelectorAll('.teacher-degree:checked')].map(c=>c.value);
      renderDegrees(prior);
    });
    position.addEventListener('change', () => card.querySelector('.teacher-position-other').classList.toggle('hidden', position.value !== 'Otro'));
    card.querySelector('.remove-row').addEventListener('click', () => card.remove());
    document.getElementById('teamList').append(card);
  }
  function restoreTeam() {
    document.getElementById('teamList').innerHTML = '';
    (payload.team || []).forEach(createTeacher);
  }
  function addAssessment(item = {}) {
    const card = document.createElement('article'); card.className = 'repeat-card assessment-card';
    card.innerHTML = `<div class="repeat-card-head"><strong>Fecha prevista</strong><button type="button" class="remove-row">Quitar</button></div><div class="field-grid three-col">
      <label>Instancia<select class="assessment-type"><option>Trabajo práctico</option><option>Parcial</option><option>Recuperatorio</option><option>Otra</option></select></label>
      <label>Fecha<input class="assessment-date" type="date"></label><label>Descripción<input class="assessment-details" placeholder="Tema, unidad o indicación"></label>
    </div>`;
    card.querySelector('.assessment-type').value = item.type || 'Trabajo práctico'; card.querySelector('.assessment-date').value = item.date || ''; card.querySelector('.assessment-details').value = item.details || '';
    card.querySelector('.remove-row').addEventListener('click',()=>card.remove()); document.getElementById('assessmentList').append(card);
  }
  function restoreRepeats() {
    document.getElementById('assessmentList').innerHTML='';
    (payload.assessments||[]).forEach(addAssessment);
  }
  function collect(stepNumber) {
    const data = {};
    if (stepNumber === 1) {
      data.career='Abogacía';
      root.querySelectorAll('[data-screen="1"] [data-key]').forEach(el => { if(el.dataset.key==='team_confirmed') data.team_confirmed=el.checked; else if(!el.disabled) data[el.dataset.key]=el.value; });
      data.subject_name=subjectSelect.selectedOptions[0]?.textContent.split(' · ').slice(1).join(' · ') || '';
      data.team=[...document.querySelectorAll('.teacher-card')].map(card=>({
        position:card.querySelector('.teacher-position').value==='Otro'?card.querySelector('.teacher-position-other').value.trim()||'Otro':card.querySelector('.teacher-position').value,
        name:card.querySelector('.teacher-name').value.trim(), prefix:card.querySelector('.teacher-prefix').value,
        degrees:[...card.querySelectorAll('.teacher-degree:checked')].map(c=>c.value==='Otro'?card.querySelector('.teacher-custom').value.trim():c.value).filter(Boolean).join(' · ')
      })).filter(x=>x.name || x.position || x.degrees);
    } else if (stepNumber === 2) {
      root.querySelectorAll('[data-screen="2"] [data-key]').forEach(el=>data[el.dataset.key]=el.value.trim());
    } else if (stepNumber === 3) {
      data.assessments=[...document.querySelectorAll('.assessment-card')].map(c=>({type:c.querySelector('.assessment-type').value,date:c.querySelector('.assessment-date').value,details:c.querySelector('.assessment-details').value.trim()})).filter(x=>x.date||x.details);
    } else if (stepNumber === 4) {
      data.consultations_confirmed=document.getElementById('consultationsConfirmed').checked;
    }
    return data;
  }
  async function save(stepNumber, advance) {
    if (stepNumber === 1 && advance && document.querySelector('.teacher-card') && !document.getElementById('teamConfirmed').checked) throw new Error('Confirmá que los nombres, cargos y títulos del equipo docente están correctos.');
    const data=collect(stepNumber); data.__advance=advance;
    const response=await fetch(`/programas/${id}/guardar/${stepNumber}/`,{method:'POST',headers:{'Content-Type':'application/json','X-CSRFToken':csrf},body:JSON.stringify(data)});
    const result=await response.json(); if(!response.ok) throw new Error(result.error||'No se pudo guardar.');
    payload={...payload,...collect(stepNumber)}; payload.subject_id=payload.subject_id||'';
    return result;
  }
  function renderReview() {
    const box=document.getElementById('reviewSummary');
    const team=(payload.team||[]).map(t=>`<p>${esc(t.position)} · ${esc(t.name)} · ${esc([t.prefix,t.degrees].filter(Boolean).join(' '))}</p>`).join('')||'<p>Equipo docente sin completar.</p>';
    const facts=[['Año académico',payload.academic_year],['Carrera','Abogacía'],['Plan',payload.plan||'2017'],['Asignatura',payload.subject_name],['Año de cursado',payload.course_year],['Turno',payload.shift],['Formato',payload.format],['Régimen',payload.term],['Carácter',payload.character],['Evaluación',payload.evaluation_type],['Carga total',payload.hours?`${payload.hours} hs.`:''],['Carga semanal',payload.weekly_hours],['Créditos',payload.credits],['Correlatividades para cursar',payload.prerequisites_to_take],['Correlatividades para rendir',payload.prerequisites_to_exam]];
    const factsHTML=facts.map(([k,v])=>`<div class="review-value"><b>${esc(k)}</b>${esc(v||'Pendiente')}</div>`).join('');
    const parts=[['Encuadre teórico / fundamentación','framing'],['Objetivo general','objectives_general'],['Objetivos específicos','objectives_specific'],['Expectativas de logro','expectations'],['Metodología','methodology'],['Unidades y contenidos','units'],['Evaluación','evaluation_text'],['Bibliografía','bibliography']].map(([label,key])=>`<div class="review-value"><b>${esc(label)}</b>${esc(payload[key]||'Pendiente')}</div>`).join('');
    const dates=(payload.assessments||[]).map(x=>`<p>${esc(x.type)} · ${esc(x.date)}${x.details?` · ${esc(x.details)}`:''}</p>`).join('')||'<p>Sin fechas cargadas.</p>';
    const consultations=payload.consultations_confirmed?'<p>Revisados y gestionados en SICDo para este año académico.</p><p><a href="https://consultas.derecho.uncu.edu.ar/horarios" target="_blank" rel="noopener noreferrer">Abrir SICDo ↗</a></p>':'<p>Pendiente de confirmar en SICDo.</p>';
    box.innerHTML=`<section class="review-block"><h3>Datos de la cátedra</h3><div class="review-grid">${factsHTML}</div></section><section class="review-block"><h3>Equipo de cátedra</h3>${team}</section><section class="review-block"><h3>Programa</h3><div class="review-grid">${parts}</div></section><section class="review-block"><h3>Fechas previstas</h3>${dates}</section><section class="review-block"><h3>Horarios de consulta</h3>${consultations}</section>`;
  }
  function show(n) {
    step=Math.max(1,Math.min(5,n));
    document.querySelectorAll('.wizard-panel').forEach(p=>p.hidden=Number(p.dataset.screen)!==step);
    document.querySelectorAll('.step-chip').forEach(a=>{const s=Number(a.dataset.stepLink);a.classList.toggle('active',s===step);a.classList.toggle('complete',s<step);});
    document.getElementById('previousStep').disabled=step===1;
    document.getElementById('nextStep').classList.toggle('hidden',step===5||readOnly);
    document.getElementById('wizardActions').classList.toggle('hidden',step===5&&readOnly);
    document.getElementById('saveDraft')?.classList.toggle('hidden',step===5);
    document.getElementById('previousStep').classList.toggle('hidden',step===5);
    if(step===5) renderReview();
    const url=new URL(location.href);url.searchParams.set('paso',step);history.replaceState({},'',url);
  }
  async function saveAndMove(advance) {
    try { await save(step,advance); if(advance) show(step+1); else alert('Borrador guardado en la bandeja común.'); }
    catch(e){alert(e.message);}
  }
  restoreScalarFields();
  if(subjectSelect.value) setSubjectDefaults(subjectSelect.selectedOptions[0],false);
  restoreTeam(); restoreRepeats();
  if(!payload.team?.length && !readOnly) createTeacher();
  if(!payload.assessments?.length) addAssessment();
  document.getElementById('addTeacher').addEventListener('click',()=>createTeacher());
  document.getElementById('addAssessment').addEventListener('click',()=>addAssessment());
  subjectSelect.addEventListener('change',()=>{setSubjectDefaults(subjectSelect.selectedOptions[0],true);});
  document.getElementById('nextStep').addEventListener('click',()=>saveAndMove(true));
  document.getElementById('saveDraft')?.addEventListener('click',()=>saveAndMove(false));
  document.getElementById('previousStep').addEventListener('click',()=>show(step-1));
  document.getElementById('submitProgram')?.addEventListener('click',async()=>{
    try {
      const result=await save(4,false);
      const response=await fetch(`/programas/${id}/enviar/`,{method:'POST',headers:{'X-CSRFToken':csrf}});
      const submitted=await response.json();if(!response.ok)throw new Error(submitted.error||'No se pudo enviar.');
      location.href=`/programas/${id}/?paso=5`;
    } catch(e){alert(e.message);}
  });
  document.querySelectorAll('.step-chip').forEach(a=>a.addEventListener('click',async event=>{
    if(readOnly)return;event.preventDefault();const target=Number(a.dataset.stepLink);
    if(target===step)return; if(target>step){try{await save(step,false);}catch(e){alert(e.message);return;}}
    show(target);
  }));
  if(readOnly) root.querySelectorAll('input,select,textarea,button').forEach(el=>{if(!['previousStep'].includes(el.id))el.disabled=true;});
  show(step);
})();
