/* BIG Solutions Management – comportamentul paginilor. Fără biblioteci externe. */
(function(){
  var BL={deschis:'Deschis',urmeaza:'Urmează',consultare:'În consultare',inchis:'Închis'};
  var WHO={F:'Firme',O:'ONG-uri',A:'Autorități'};
  function $(s,r){return (r||document).querySelector(s);}
  function $$(s,r){return Array.prototype.slice.call((r||document).querySelectorAll(s));}
  function el(tag,cls,txt){var e=document.createElement(tag);if(cls)e.className=cls;if(txt!=null)e.textContent=txt;return e;}
  function badge(s){return el('span','bdg b-'+s,BL[s]);}
  function when(c){if(c.when)return c.when;if(c.s==='deschis')return 'termen '+c.close;if(c.s==='urmeaza')return c.open?'se deschide la '+c.open:'dată neanunțată';return 'închis la '+c.close;}

  /* meniul pe telefon */
  var burger=$('#burger'),mnav=$('#mnav');
  if(burger&&mnav)burger.addEventListener('click',function(){mnav.hidden=!mnav.hidden;burger.setAttribute('aria-expanded',String(!mnav.hidden));});

  /* prima pagină: filtrul programelor */
  var pf=$('#pfilter');
  if(pf)$$('button',pf).forEach(function(b){b.addEventListener('click',function(){
    $$('button',pf).forEach(function(x){x.setAttribute('aria-pressed',String(x===b));});
    $$('#progs .prog').forEach(function(a){a.hidden=!(b.dataset.f==='all'||(a.dataset.t||'').split(' ').indexOf(b.dataset.f)>-1);});
  });});

  /* calendarul apelurilor */
  var crows=$('#crows');
  if(crows&&window.CALLS){
    var calls=window.CALLS,psel=$('#cf-prog'),seen={},ix=document.body.dataset.ix||'';
    calls.forEach(function(c){var p=c.prog[0];if(!seen[p]){seen[p]=1;var o=document.createElement('option');o.value=p;o.textContent=p;psel.appendChild(o);}});
    var CRANK={deschis:0,urmeaza:1,consultare:2,inchis:3},cpage=1;
    function cur(id){var b=$('#'+id+' button[aria-pressed="true"]');return b?b.dataset.v:'all';}
    function setChip(id,v){$$('#'+id+' button').forEach(function(b){b.setAttribute('aria-pressed',String(b.dataset.v===v));});}
    function dkey(d){return d?d.split('.').reverse().join(''):'99999999';}
    function nApel(n){var r=n%100;return n===1?'1 apel':n+((n>=20&&(r===0||r>=20))?' de apeluri':' apeluri');}
    function pageSize(){var v=cur('cf-n');return v==='all'?Infinity:+v;}
    /* căutarea ignoră diacriticele: „stocare”, „ștocare” și „STOCARE” găsesc același lucru */
    function plain(t){return t.toLowerCase().normalize('NFD').replace(/[\u0300-\u036f]/g,'');}
    var qin=$('#cf-q');function words(){return qin?plain(qin.value).split(/\s+/).filter(Boolean):[];}
    function link(c,txt){var a=el('a','link',txt);a.href=c.slug+'/'+ix;return a;}
    function renderPager(pages){
      var nav=$('#cpager');nav.textContent='';nav.hidden=pages<2;if(pages<2)return;
      function btn(label,page,o){var b=el('button',null,label);b.type='button';if(o.cur)b.setAttribute('aria-current','page');if(o.dis)b.disabled=true;b.setAttribute('aria-label',o.aria);
        b.addEventListener('click',function(){cpage=page;render(true);$('.ctable').scrollIntoView({block:'start'});});return b;}
      var prev=btn('',cpage-1,{dis:cpage===1,aria:'Pagina anterioară'});prev.innerHTML='←<span class="lbl-t"> Înapoi</span>';nav.appendChild(prev);
      var nums=[1];for(var k=Math.max(2,cpage-1);k<=Math.min(pages-1,cpage+1);k++)nums.push(k);nums.push(pages);
      var last=0;nums.forEach(function(n){if(n-last>1)nav.appendChild(el('span','gap','…'));nav.appendChild(btn(String(n),n,{cur:n===cpage,aria:'Pagina '+n}));last=n;});
      var next=btn('',cpage+1,{dis:cpage===pages,aria:'Pagina următoare'});next.innerHTML='<span class="lbl-t">Înainte </span>→';nav.appendChild(next);
    }
    function render(keep){
      var w=cur('cf-who'),s=cur('cf-st'),p=psel.value,q=words();crows.textContent='';
      if(!keep)cpage=1;
      var list=calls.filter(function(c){return (w==='all'||c.w.indexOf(w)>-1)&&(s==='all'||c.s===s)&&(p==='all'||c.prog[0]===p)&&q.every(function(x){return c.q.indexOf(x)>-1;});});
      list.sort(function(x,y){var a=dkey(x.close),b=dkey(y.close);return (CRANK[x.s]-CRANK[y.s])||(x.s==='inchis'?(a<b?1:a>b?-1:0):(a<b?-1:a>b?1:0));});
      var size=pageSize(),total=list.length,pages=size===Infinity?1:Math.max(1,Math.ceil(total/size));
      if(cpage>pages)cpage=pages;
      var from=size===Infinity?0:(cpage-1)*size,vis=list.slice(from,from+size);
      $('#ccount').textContent=(pages>1?'Afișăm '+(from+1)+'–'+(from+vis.length)+' din '+nApel(total):nApel(total))+(q.length?' pentru „'+qin.value.trim()+'”':'');
      renderPager(pages);
      if(!list.length){crows.appendChild(el('div','empty',q.length?'Niciun apel nu se potrivește cu „'+qin.value.trim()+'”. Încercați alt cuvânt sau ștergeți căutarea.':'Niciun apel pentru filtrele alese. Schimbați solicitantul, programul sau starea.'));return;}
      vis.forEach(function(c){
        var r=el('div','crow');r.setAttribute('role','row');
        var c1=el('div');var t=el('div','t');t.appendChild(link(c,c.n));c1.appendChild(t);c1.appendChild(el('div','f',c.prog.join(' · ')));r.appendChild(c1);
        var c2=el('div','w');c.w.forEach(function(x){c2.appendChild(el('span','tag',WHO[x]));});r.appendChild(c2);
        var c3=el('div','d');c3.appendChild(badge(c.s));c3.appendChild(el('small',null,when(c)));r.appendChild(c3);
        r.appendChild(el('div','s',c.sum));
        var c5=el('div','x');c5.appendChild(link(c,'Fișa apelului'));r.appendChild(c5);
        crows.appendChild(r);
      });
    }
    ['cf-who','cf-st','cf-n'].forEach(function(id){$$('#'+id+' button').forEach(function(b){b.addEventListener('click',function(){setChip(id,b.dataset.v);render();});});});
    psel.addEventListener('change',function(){render();});
    if(qin){qin.addEventListener('input',function(){render();});qin.addEventListener('keydown',function(e){if(e.key==='Escape'){qin.value='';render();}});}
    render();
  }

  /* formularul de eligibilitate, în 4 pași */
  var ef=$('#ef');
  if(ef){
    var judete=['Alba','Arad','Argeș','Bacău','Bihor','Bistrița-Năsăud','Botoșani','Brașov','Brăila','București','Buzău','Caraș-Severin','Călărași','Cluj','Constanța','Covasna','Dâmbovița','Dolj','Galați','Giurgiu','Gorj','Harghita','Hunedoara','Ialomița','Iași','Ilfov','Maramureș','Mehedinți','Mureș','Neamț','Olt','Prahova','Satu Mare','Sălaj','Sibiu','Suceava','Teleorman','Timiș','Tulcea','Vaslui','Vâlcea','Vrancea'];
    var ce={
      firma:['Vehicule electrice','Stații de încărcare','Panouri fotovoltaice sau baterii','Utilaje și producție','Tehnologie și inovare','Agricultură și procesare','Clădiri și eficiență energetică','Altceva'],
      ong:['Servicii sociale','Educație, formare și ocupare','Cultură, turism și patrimoniu','Dotări și clădiri','Digitalizare','Altceva'],
      uat:['Fotovoltaice cu stocare','Iluminat public','Apă-canal','Clădiri și eficiență energetică','Servicii sociale','Mobilitate și stații de încărcare','Altceva']
    };
    ce.noua=ce.firma;ce.alta=ce.uat;
    var jsel=$('#judet');judete.forEach(function(j){var o=document.createElement('option');o.textContent=j;jsel.appendChild(o);});
    function goStep(n){
      $$('#ef [data-step]').forEach(function(c){c.hidden=(+c.dataset.step!==n);});
      $('#ef-num').textContent='Pasul '+n+' din 4';
      $$('.prog-bar i').forEach(function(i,k){i.classList.toggle('on',k<n);});
    }
    function tip(){var r=$('input[name=tip]:checked');return r?r.value:'';}
    function onTip(){
      var t=tip();$('#marime-f').hidden=(t!=='firma');$('#e1').hidden=true;
      var box=$('#ce-opts');box.textContent='';
      (ce[t]||[]).forEach(function(o,k){var l=el('label','opt');var i=document.createElement('input');i.type='checkbox';i.name='ce';i.id='ce-'+k;i.value=o;l.appendChild(i);l.appendChild(el('span',null,o));box.appendChild(l);});
    }
    function err(id,msg){var e=$('#'+id);if(msg)e.textContent=msg;e.hidden=false;}
    function ok(id){$('#'+id).hidden=true;}
    $$('input[name=tip]').forEach(function(r){r.addEventListener('change',onTip);});
    $$('[data-next]').forEach(function(b){b.addEventListener('click',function(){
      var n=+b.dataset.next;
      if(n===1){if(!tip()){err('e1');return;}ok('e1');}
      if(n===2){if(!$('input[name=ce]:checked')){err('e2');return;}ok('e2');}
      if(n===3){var j=$('#judet'),v=$('#valoare');j.setAttribute('aria-invalid',String(!j.value));v.setAttribute('aria-invalid',String(!v.value));if(!j.value||!v.value){err('e3');return;}ok('e3');}
      goStep(n+1);
    });});
    $$('[data-back]').forEach(function(b){b.addEventListener('click',function(){goStep(+b.dataset.back-1);});});
    $$('#ce-opts, #judet, #valoare').forEach(function(x){x.addEventListener('change',function(){ok('e2');ok('e3');});});
    ['nume','tel','email'].forEach(function(id){$('#'+id).addEventListener('input',function(){this.removeAttribute('aria-invalid');ok('e4');});});
    $('#gdpr').addEventListener('change',function(){ok('e4');});
    ef.addEventListener('submit',function(e){
      e.preventDefault();
      var nume=$('#nume'),tel=$('#tel'),em=$('#email'),g=$('#gdpr'),miss=[];
      if(!nume.value.trim()){miss.push('numele');nume.setAttribute('aria-invalid','true');}
      if(tel.value.replace(/\D/g,'').length<10){miss.push('un număr de telefon de 10 cifre');tel.setAttribute('aria-invalid','true');}
      if(!/^\S+@\S+\.\S+$/.test(em.value.trim())){miss.push('o adresă de e-mail validă');em.setAttribute('aria-invalid','true');}
      if(miss.length){err('e4','Completați '+miss.join(', ')+'.');return;}
      if(!g.checked){err('e4','Bifați acordul pentru prelucrarea datelor, ca să vă putem contacta.');return;}
      $('#ef-steps').hidden=true;$('#ef-done').hidden=false;
    });
    function resetForm(){ef.reset();$('#ef-steps').hidden=false;$('#ef-done').hidden=true;['e1','e2','e3','e4'].forEach(ok);$$('#ef [aria-invalid]').forEach(function(x){x.removeAttribute('aria-invalid');});onTip();goStep(1);}
    $('#ef-again').addEventListener('click',resetForm);
    var pre=new URLSearchParams(location.search).get('tip'),r=pre&&document.getElementById('tip-'+pre);
    if(r){r.checked=true;onTip();}
  }

  /* formularul de contact */
  var cf=$('#cform');
  if(cf)cf.addEventListener('submit',function(e){
    e.preventDefault();
    var good=['c-nume','c-ct','c-msg'].every(function(id){return $('#'+id).value.trim();})&&$('#c-gdpr').checked;
    $('#c-err').hidden=good;if(good){cf.hidden=true;$('#c-done').hidden=false;}
  });

  /* fișa e-DRIVE, de pe prima pagină */
  var mf=$('#mform');
  if(mf){
    mf.addEventListener('submit',function(e){
      e.preventDefault();var v=$('#m-email').value.trim(),m=$('#m-msg');
      if(!/^\S+@\S+\.\S+$/.test(v)){m.textContent='Scrieți o adresă de e-mail validă, de exemplu nume@firma.ro.';return;}
      m.textContent='Mulțumim! Vă trimitem fișa pe e-mail.';
    });
    $('#m-email').addEventListener('input',function(){$('#m-msg').textContent='';});
  }
})();
