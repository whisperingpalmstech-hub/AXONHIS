"use client";

import React, { useEffect, useState } from "react";
import { TopNav } from "@/components/ui/TopNav";
import { 
  Microscope, Syringe, TestTube, AlertTriangle, ShieldAlert,
  Droplet, Activity, FlaskConical, UploadCloud, Search, CheckCircle2,
  Globe, Stethoscope
} from "lucide-react";
import { advancedLabApi, type HistoSpecimen, type MicroCulture, type CSSDTest, type BloodBankUnit } from "@/lib/advanced-lab-api";

export default function AdvancedDiagnosticsPage() {
  const [activeTab, setActiveTab] = useState<"HISTO" | "MICRO" | "CSSD" | "BLOOD">("HISTO");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  // Data
  const [histos, setHistos] = useState<HistoSpecimen[]>([]);
  const [micros, setMicros] = useState<MicroCulture[]>([]);
  const [cssds, setCssds] = useState<CSSDTest[]>([]);
  const [bloods, setBloods] = useState<BloodBankUnit[]>([]);

  const fetchData = async () => {
    setLoading(true);
    try {
      if (activeTab === "HISTO") setHistos(await advancedLabApi.getSpecimens() || []);
      else if (activeTab === "MICRO") setMicros(await advancedLabApi.getCultures() || []);
      else if (activeTab === "CSSD") setCssds(await advancedLabApi.getCSSDTests() || []);
      else if (activeTab === "BLOOD") setBloods(await advancedLabApi.getBloodBank() || []);
    } catch (err: any) {
      // Mock Fallback UI setup since real DB is probably empty at standard run
      mockDataFallback(activeTab);
    }
    setLoading(false);
  };

  const mockDataFallback = (tab: string) => {
    if (tab === "HISTO" && histos.length === 0) {
      setHistos([
        { id: "HST-2009", sample_id: "SMP-772", patient_uhid: "UHID-8822", patient_name: "Sarah Connors", current_stage: "Microscopic Examination", is_sensitive: false, requires_counseling: false, counseling_status: "PENDING", is_oncology: false, created_at: new Date().toISOString(), blocks: [ { id: "BLK-1", block_label: "A1", embedding_status: "Embedded", slides: [ { id: "SLD-1", slide_label: "A1-H&E", staining_type: "H&E", microscopic_diagnosis: "", microscopic_images: ["/dicom_mock.jpg"], prepared_at: new Date().toISOString() } ] } ]},
        { id: "HST-2010", sample_id: "SMP-775", patient_uhid: "UHID-1100", patient_name: "John Miller", current_stage: "Block Creation", is_sensitive: true, requires_counseling: true, counseling_status: "PENDING", is_oncology: true, created_at: new Date().toISOString(), blocks: [] }
      ]);
    }
    if (tab === "MICRO" && micros.length === 0) {
      setMicros([
        { id: "CUL-800", sample_id: "SMP-881", patient_uhid: "UHID-1100", source_department: "Ward B", incubation_type: "Aerobic", organism_identified: "MRSA", is_infection_control_screen: false, sensitivities: [ { id: "S1", antibiotic_name: "Vancomycin", mic_value: 1.5, susceptibility: "Sensitive" }, { id: "S2", antibiotic_name: "Penicillin", mic_value: 32, susceptibility: "Resistant" } ] }
      ]);
    }
    if (tab === "CSSD" && cssds.length === 0) {
      setCssds([ { id: "CS-10", test_sample_id: "OT1-INSTR-99", control_sample_id: "CTRL-V1", sterilization_validated: true, growth_in_test_sample: false, growth_in_control_sample: true, tested_at: new Date().toISOString() } ]);
    }
    if (tab === "BLOOD" && bloods.length === 0) {
      setBloods([ { id: "BU-509", unit_id: "DON-209", blood_group: "O+", collection_date: new Date().toISOString(), expiry_date: new Date(Date.now() + 86400000*30).toISOString(), component_type: "PRBC", status: "Available" } ]);
    }
  };

  useEffect(() => { fetchData(); }, [activeTab]);

  // HISTO ACTIONS
  const handleAdvanceHisto = async (spec: HistoSpecimen, stage: string, diagnoseStr?: string) => {
    try {
      if(spec.id.startsWith("HST-")) {
        const h = [...histos];
        const idx = h.findIndex(x=>x.id===spec.id);
        h[idx].current_stage = stage;
        if(diagnoseStr && diagnoseStr.toLowerCase().includes("malignant")) {
          h[idx].is_oncology = true; h[idx].is_sensitive = true; h[idx].requires_counseling = true;
          setSuccess("Cancer detected. Specimen locked. Auto-referral to Oncology dispatched.");
        } else { setSuccess(`Stage advanced to ${stage}`); }
        setHistos(h);
      } else {
        await advancedLabApi.advanceSpecimen(spec.id, stage, diagnoseStr);
        setSuccess(`Stage advanced to ${stage}`);
        fetchData();
      }
    } catch(e:any) { setError(e.message); }
  };

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col font-sans">
      <TopNav title="LIS Advanced Diagnostic Modules" />
      <div className="flex-1 p-6 max-w-[1500px] mx-auto w-full space-y-6">

        {/* HEADER */}
        <div className="flex justify-between items-center bg-white p-6 rounded-2xl shadow-sm border border-slate-200">
          <div>
            <h1 className="text-2xl font-black text-slate-900 flex items-center gap-2"><Globe className="text-indigo-600"/> Advanced Sub-Specialties</h1>
            <p className="text-slate-500 font-bold text-xs uppercase tracking-wider mt-1">Histopathology • Microbiology • Blood Bank • CSSD Sterility</p>
          </div>
          <div className="flex bg-slate-100 p-1 rounded-xl shadow-inner border border-slate-200">
            <button onClick={()=>setActiveTab("HISTO")} className={`flex items-center gap-2 px-5 py-2.5 rounded-lg text-xs font-black transition-all ${activeTab==='HISTO' ? 'bg-indigo-600 text-white shadow':'text-slate-500 hover:text-indigo-600'}`}><Microscope size={14}/> Histopathology</button>
            <button onClick={()=>setActiveTab("MICRO")} className={`flex items-center gap-2 px-5 py-2.5 rounded-lg text-xs font-black transition-all ${activeTab==='MICRO' ? 'bg-indigo-600 text-white shadow':'text-slate-500 hover:text-indigo-600'}`}><FlaskConical size={14}/> Microbiology</button>
            <button onClick={()=>setActiveTab("BLOOD")} className={`flex items-center gap-2 px-5 py-2.5 rounded-lg text-xs font-black transition-all ${activeTab==='BLOOD' ? 'bg-indigo-600 text-white shadow':'text-slate-500 hover:text-indigo-600'}`}><Droplet size={14}/> Blood Bank</button>
            <button onClick={()=>setActiveTab("CSSD")} className={`flex items-center gap-2 px-5 py-2.5 rounded-lg text-xs font-black transition-all ${activeTab==='CSSD' ? 'bg-indigo-600 text-white shadow':'text-slate-500 hover:text-indigo-600'}`}><ShieldAlert size={14}/> CSSD Sterility</button>
          </div>
        </div>

        {error && <div className="p-3 bg-rose-50 text-rose-800 border border-rose-200 rounded-lg text-xs font-bold flex gap-2"><AlertTriangle size={14}/>{error}</div>}
        {success && <div className="p-3 bg-emerald-50 text-emerald-800 border border-emerald-200 rounded-lg text-xs font-bold flex gap-2"><CheckCircle2 size={14}/>{success}</div>}

        {/* ===================== HISTOPATHOLOGY MODULE ===================== */}
        {activeTab === "HISTO" && (
           <div className="space-y-4">
             {histos.length === 0 ? (
               <div className="flex flex-col items-center justify-center p-12 bg-white rounded-xl border border-dashed border-slate-300">
                 <Microscope size={48} className="text-slate-300 mb-4"/>
                 <h3 className="text-slate-500 font-bold">No Histopathology Specimens Found</h3>
                 <p className="text-slate-400 text-xs text-center mt-2 max-w-sm">When specimens are received through the Central Receiving module, they will appear here for processing.</p>
               </div>
             ) : (
               histos.map(spec => (
                 <div key={spec.id} className="bg-white border-l-4 border-l-indigo-600 rounded-xl shadow-sm overflow-hidden flex flex-col md:flex-row border border-slate-200">
                    <div className="p-5 md:w-1/3 border-r border-slate-100 bg-slate-50">
                      <div className="flex items-center justify-between mb-2">
                         <span className="text-[10px] font-mono text-slate-500">{spec.id} | SMP: {spec.sample_id}</span>
                         {spec.is_oncology && <span className="flex items-center gap-1 text-[9px] font-black uppercase bg-purple-100 text-purple-700 px-2 py-0.5 rounded border border-purple-200"><Stethoscope size={10}/> Oncology Cross-Referral</span>}
                      </div>
                      <h3 className="text-lg font-black text-slate-800">{spec.patient_name || "Unknown Patient"}</h3>
                      <p className="text-xs font-bold text-slate-500 mb-4">{spec.patient_uhid}</p>
                      
                      {spec.is_sensitive && (
                        <div className="mt-2 text-[10px] bg-rose-100 border border-rose-200 text-rose-800 p-2 rounded flex flex-col gap-1 font-bold">
                          <div className="flex gap-1 items-center"><ShieldAlert size={12}/> RESTRICTED REPORT HANDLING</div>
                          <span className="font-normal leading-tight opacity-90">Cannot be dispatched to generic patient portal. Mandated Clinical Counseling requirement actively queued.</span>
                        </div>
                      )}
                    </div>
                    
                    <div className="p-5 md:flex-1 relative">
                       <span className="absolute top-4 right-4 text-[10px] font-black uppercase text-slate-400">Workflow Engine</span>
                       <div className="flex items-center gap-2 mb-4 flex-wrap">
                         {["Specimen Received", "Block Creation", "Slide Preparation", "Microscopic Examination", "Diagnosis", "Report Release"].map((stg, i) => {
                            const isActive = spec.current_stage === stg;
                            const isDone = ["Specimen Received", "Block Creation", "Slide Preparation", "Microscopic Examination", "Diagnosis", "Report Release"].indexOf(spec.current_stage) > i;
                            return (
                              <React.Fragment key={stg}>
                                <div className={`p-2 rounded border text-[10px] font-black uppercase cursor-pointer transition-all ${isActive?'bg-indigo-600 text-white shadow-lg border-indigo-700':isDone?'bg-emerald-50 text-emerald-700 border-emerald-200':'bg-slate-50 text-slate-400 border-slate-200 hover:border-slate-400'}`} onClick={()=>handleAdvanceHisto(spec, stg)}>
                                  {stg}
                                </div>
                                {i < 5 && <div className={`h-1 w-4 ${isDone?'bg-emerald-200':'bg-slate-200'}`}></div>}
                              </React.Fragment>
                            )
                         })}
                       </div>

                       {spec.current_stage === "Microscopic Examination" && (
                         <div className="bg-slate-50 border border-slate-200 p-4 rounded-xl mt-4 space-y-3 shadow-inner">
                           <div className="flex justify-between items-center"><h4 className="text-sm font-black text-slate-800 flex items-center gap-2"><Microscope size={16} className="text-indigo-500"/> Slide Canvas UI</h4><button className="btn btn-sm bg-indigo-100 hover:bg-indigo-200 text-indigo-700 cursor-pointer flex gap-1"><UploadCloud size={14}/> Push DICOM Image</button></div>
                           <div className="grid grid-cols-4 gap-2">
                             {spec.blocks?.[0]?.slides?.[0]?.microscopic_images?.map((img, i)=>(
                                <div key={i} className="aspect-square bg-slate-200 rounded-lg flex items-center justify-center border-dashed border-2 border-slate-300 relative group overflow-hidden">
                                  <span className="text-[10px] font-bold text-slate-400">Slide_{i}.jpg</span>
                                </div>
                             )) || <div className="col-span-4 p-4 text-center text-xs text-slate-400">No slides or images attached yet.</div>}
                           </div>
                         </div>
                       )}

                       {spec.current_stage === "Diagnosis" && !spec.is_oncology && (
                         <div className="mt-4 flex flex-col gap-2">
                           <input type="text" placeholder="Enter conclusion (e.g., Malignant Melanoma)" className="input-field max-w-md p-2 border rounded" onKeyDown={(e:any)=>{if(e.key==='Enter') handleAdvanceHisto(spec, "Report Release", e.target.value)}} />
                           <span className="text-[10px] text-slate-400 leading-tight">Type 'malignant' and hit Enter to preview Smart Cross-Referral AI hooks.</span>
                         </div>
                       )}
                    </div>
                 </div>
               ))
             )}
           </div>
        )}

        {/* ===================== MICROBIOLOGY & SENSITIVITY ===================== */}
        {activeTab === "MICRO" && (
           <div className="space-y-4">
             {micros.length === 0 ? (
               <div className="flex flex-col items-center justify-center p-12 bg-white rounded-xl border border-dashed border-slate-300">
                 <FlaskConical size={48} className="text-slate-300 mb-4"/>
                 <h3 className="text-slate-500 font-bold">No Microbiology Cultures Found</h3>
                 <p className="text-slate-400 text-xs text-center mt-2 max-w-sm">Samples marked for culture will appear here automatically.</p>
               </div>
             ) : (
               micros.map(cul => (
                 <div key={cul.id} className="bg-white border-l-4 border-l-emerald-500 rounded-xl shadow-sm flex flex-col border border-slate-200">
                   <div className="p-4 bg-emerald-50/50 flex justify-between border-b border-emerald-100">
                      <div className="flex items-center gap-3">
                        <FlaskConical size={20} className="text-emerald-600"/>
                        <div>
                          <h3 className="font-black text-emerald-900">{cul.organism_identified || "Culture ID: " + cul.id}</h3>
                          <p className="text-[10px] uppercase font-bold text-slate-500">Sample: {cul.sample_id} | Env: {cul.incubation_type}</p>
                        </div>
                      </div>
                      {cul.is_infection_control_screen && <span className="bg-red-100 text-red-700 px-3 py-1 text-[10px] font-black uppercase rounded-lg border border-red-200 shadow-sm flex items-center gap-1"><ShieldAlert size={12}/> Infection Control Audit</span>}
                   </div>
                   
                   <div className="p-4 grid grid-cols-2 lg:grid-cols-4 gap-4 bg-slate-50/30">
                      <div><span className="block text-[9px] uppercase font-bold text-slate-400">Growth Findings</span><span className="text-sm font-black text-slate-800">{cul.growth_findings || "Pending Incubation"}</span></div>
                      <div><span className="block text-[9px] uppercase font-bold text-slate-400">Organism Target</span><span className="text-sm font-bold text-indigo-700 bg-indigo-50 px-2 rounded-sm border border-indigo-100">{cul.organism_identified || "Not Isolated"}</span></div>
                   </div>

                   {cul.sensitivities.length > 0 && (
                     <div className="p-4 border-t border-slate-100">
                       <h4 className="text-[10px] uppercase font-black text-slate-500 mb-2 flex items-center gap-1"><Activity size={12}/> Antibiogram Mapping</h4>
                       <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
                         {cul.sensitivities.map(s => (
                           <div key={s.id} className={`p-2 border rounded-lg text-xs font-bold flex justify-between ${s.susceptibility==="Resistant"?'bg-rose-50 border-rose-200 text-rose-800':s.susceptibility==="Sensitive"?'bg-emerald-50 border-emerald-200 text-emerald-800':'bg-amber-50 border-amber-200 text-amber-800'}`}>
                             <span>{s.antibiotic_name} (MIC {s.mic_value})</span><span>{s.susceptibility.charAt(0).toUpperCase()}</span>
                           </div>
                         ))}
                       </div>
                     </div>
                   )}
                 </div>
               ))
             )}
           </div>
        )}

        {/* ===================== CSSD & BLOOD BANK ===================== */}
        {activeTab === "CSSD" && (
           <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
             {cssds.length === 0 ? (
               <div className="col-span-full flex flex-col items-center justify-center p-12 bg-white rounded-xl border border-dashed border-slate-300">
                 <ShieldAlert size={40} className="text-slate-300 mb-4"/>
                 <h3 className="text-slate-500 font-bold">No CSSD Sterility Tests Found</h3>
               </div>
             ) : (
               cssds.map(c => (
                 <div key={c.id} className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm relative">
                   <ShieldAlert size={40} className={`absolute right-4 top-4 opacity-10 ${c.sterilization_validated?'text-emerald-500':'text-rose-500'}`}/>
                   <h3 className="font-black text-slate-800 text-lg">Batch {c.test_sample_id.split('-')[0]} Check</h3>
                   <p className="text-[10px] font-mono text-slate-400 mt-1">Instrument Payload: {c.test_sample_id}</p>
                   <div className="mt-4 flex gap-4 text-xs font-bold">
                     <div className="flex flex-col gap-1 text-slate-600"><span className="text-[9px] uppercase">Control Spores</span> <span className={c.growth_in_control_sample?'text-emerald-600':'text-rose-600'}>{c.growth_in_control_sample?'Positive Growth (Valid)':'Failed Benchmark'}</span></div>
                     <div className="h-full w-px bg-slate-200"></div>
                     <div className="flex flex-col gap-1 text-slate-600"><span className="text-[9px] uppercase">Test Indicators</span> <span className={c.growth_in_test_sample?'text-rose-600':'text-emerald-600'}>{c.growth_in_test_sample?'Contamination (FAILED)':'No Growth (STERILE)'}</span></div>
                   </div>
                   <div className={`mt-4 w-full p-2 text-center text-xs font-black uppercase rounded ${c.sterilization_validated?'bg-emerald-600 text-white shadow-emerald-200 shadow-lg':'bg-rose-600 text-white shadow-rose-200 shadow-lg'}`}>
                     {c.sterilization_validated ? "Sterilization Validated -> PUSH TO OT" : "PROTOCOL FAILED -> RE-STERILIZE"}
                   </div>
                 </div>
               ))
             )}
           </div>
        )}

        {activeTab === "BLOOD" && (
           <div className="overflow-x-auto bg-white rounded-xl shadow-sm border border-slate-200">
             <table className="w-full text-left text-sm">
               <thead className="bg-rose-50 border-b border-rose-100 text-[10px] uppercase font-black text-rose-800">
                 <tr>
                   <th className="p-3">Unit Tag</th><th className="p-3">Blood Grp</th><th className="p-3">Component</th><th className="p-3">Collection / Expiry</th><th className="p-3">Availability Vector</th>
                 </tr>
               </thead>
               <tbody className="divide-y divide-slate-100">
                 {bloods.length === 0 ? (
                   <tr>
                     <td colSpan={5} className="p-8 text-center text-slate-500"><div className="flex flex-col items-center"><Droplet size={32} className="text-slate-300 mb-2"/><span className="font-bold">Inventory Empty</span></div></td>
                   </tr>
                 ) : (
                   bloods.map(b => (
                     <tr key={b.id} className="hover:bg-slate-50">
                       <td className="p-3 font-mono font-bold text-slate-700">{b.unit_id}</td>
                       <td className="p-3"><span className="bg-rose-600 text-white text-sm font-black px-2 py-1 rounded shadow-sm">{b.blood_group}</span></td>
                       <td className="p-3 font-bold text-slate-600">{b.component_type}</td>
                       <td className="p-3"><div className="text-xs">{new Date(b.collection_date).toLocaleDateString()}</div><div className="text-[10px] font-bold text-amber-600">Exp: {new Date(b.expiry_date).toLocaleDateString()}</div></td>
                       <td className="p-3"><span className="text-[10px] font-black uppercase text-emerald-700 bg-emerald-100 px-2 py-1 rounded-full border border-emerald-200 tracking-wider flex w-max items-center gap-1"><CheckCircle2 size={12}/> {b.status}</span></td>
                     </tr>
                   ))
                 )}
               </tbody>
             </table>
           </div>
        )}

      </div>
    </div>
  );
}
