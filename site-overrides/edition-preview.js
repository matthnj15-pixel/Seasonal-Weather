/* Interactive holiday preview. This is sample artwork; the installed
   widget itself uses the local date and real weather. */
(() => {
  "use strict";
  const editions = [
    {key:"july4",name:"Fourth of July",detail:"Fireworks and summer bunting"},
    {key:"christmas",name:"Christmas",detail:"Evergreen lights and ornaments"},
    {key:"newyear",name:"New Year's",detail:"Gold confetti and fireworks"},
    {key:"easter",name:"Easter",detail:"Spring blossoms and painted eggs"},
    {key:"thanksgiving",name:"Thanksgiving",detail:"Autumn harvest accents"},
    {key:"halloween",name:"Halloween",detail:"Pumpkins, bats, and lanterns"},
    {key:"memorial",name:"Memorial Day",detail:"Poppies and patriotic details"},
    {key:"labor",name:"Labor Day",detail:"Summer kites and bunting"},
    {key:"birthday_a",name:"Birthday · October 6",detail:"Warm golden celebration"},
    {key:"birthday_b",name:"Birthday · July 9",detail:"Bright summer celebration"}
  ];
  window.SeasonalEditionPreview={selectedEdition:"standard"};
  const controls=document.querySelector(".controls-panel");
  if(!controls)return;

  const picker=document.createElement("div");
  picker.className="control-group edition-picker";
  picker.innerHTML='<div class="control-title">Special editions <span>OPTIONAL PREVIEW</span></div><label class="edition-input-label" for="edition-select">Preview one of the 10 date-aware editions</label><div class="edition-select-shell"><select id="edition-select" aria-label="Choose special edition"><option value="standard">Standard seasonal weather</option></select><span aria-hidden="true">⌄</span></div><p class="edition-picker-note">The installed widget automatically switches on matching dates. This selector is only for exploring the artwork.</p>';
  const select=picker.querySelector("select");
  editions.forEach(item=>{
    const option=document.createElement("option");
    option.value=item.key;
    option.textContent=item.name;
    select.appendChild(option);
  });
  const seasonGroup=controls.querySelector(".control-group");
  if(seasonGroup) seasonGroup.after(picker);
  else controls.append(picker);

  const section=document.createElement("section");
  section.className="holiday-gallery-section section container";
  section.id="holiday-editions";
  section.innerHTML='<div class="landscapes-head"><div><div class="section-kicker">THE SPECIAL EDITIONS</div><h2>Good days deserve<br><em>a different sky.</em></h2><p>Ten event themes, each adapted to the forecast and the light outside. Available in both small and medium.</p></div><span class="demo-label">Automatic on the date</span></div><div class="holiday-gallery" role="group" aria-label="Holiday artwork previews"></div>';
  const gallery=section.querySelector(".holiday-gallery");
  const galleryButtons=[];
  for(const item of editions) {
    const button=document.createElement("button");
    button.type="button";
    button.className="holiday-tile";
    button.dataset.edition=item.key;
    button.setAttribute("aria-label","Preview "+item.name+" scenery");
    const photo=document.createElement("img");
    photo.loading="lazy";
    photo.decoding="async";
    photo.src="assets/backgrounds/holiday_"+item.key+"_sunny_day.jpg";
    photo.alt=item.detail;
    const title=document.createElement("strong");
    title.textContent=item.name;
    const desc=document.createElement("small");
    desc.textContent=item.detail;
    const info=document.createElement("span");
    info.className="holiday-caption";
    info.append(title,desc);
    button.append(photo,info);
    button.addEventListener("click",()=>{
      select.value=item.key;
      changeEdition(item.key);
      const explorer=document.getElementById("explore") || document.querySelector(".explorer");
      explorer?.scrollIntoView({behavior:matchMedia("(prefers-reduced-motion: reduce)").matches?"instant":"smooth",block:"start"});
    });
    gallery.append(button);
    galleryButtons.push(button);
  }
  const before=document.querySelector(".installation");
  if(before) before.before(section);
  else document.querySelector("main")?.append(section);

  function changeEdition(key){
    window.SeasonalEditionPreview.selectedEdition=key;
    galleryButtons.forEach(button=>button.setAttribute("aria-pressed",String(button.dataset.edition===key)));
    const hint=document.querySelector(".mobile-scene-preview small");
    if(hint) hint.textContent=key==="standard"?"Changes as you choose conditions":"Special edition artwork preview";
    window.dispatchEvent(new CustomEvent("sw-edition-change",{detail:{edition:key}}));
  }
  select.addEventListener("change",()=>changeEdition(select.value));
  changeEdition("standard");
})();
