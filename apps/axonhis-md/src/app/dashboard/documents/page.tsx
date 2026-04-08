"use client";
import React, { useState, useEffect, useCallback } from "react";
import { TopNav } from "@/components/TopNav";
import { API, authHeaders, apiFetch, apiPost } from "@/lib/api";

const apiDelete = async (endpoint: string) => {
  const res = await fetch(`${API}${endpoint}`, {
    method: "DELETE",
    headers: authHeaders()
  });
  if (!res.ok) throw new Error("Delete failed");
  return res.json();
};

export default function Page() {
  const [items, setItems] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [form, setForm] = useState<any>({ category: "GENERAL" });
  const [saving, setSaving] = useState(false);
  const [encounters, setEncounters] = useState<any[]>([]);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [dragActive, setDragActive] = useState(false);

  const load = useCallback(async () => {
    try { 
      const data = await apiFetch("/documents"); 
      setItems(data); 
      const encs = await apiFetch("/encounters");
      setEncounters(encs);
    } catch { setItems([]); }
    finally { setLoading(false); }
  }, []);
  useEffect(() => { load(); }, [load]);

  const handleCreate = async () => {
    setSaving(true);
    try {
      let storageUri = "";
      let mimeType = null;
      
      // Upload file if selected
      if (selectedFile) {
        const formData = new FormData();
        formData.append("file", selectedFile);
        
        const uploadRes = await fetch(`${API}/documents/upload`, {
          method: "POST",
          headers: authHeaders(),
          body: formData
        });
        if (!uploadRes.ok) throw new Error("File upload failed");
        const uploadData = await uploadRes.json();
        storageUri = uploadData.storage_uri;
        mimeType = selectedFile.type;
      }
      
      await apiPost("/documents", {
        encounter_id: form.encounter_id,
        document_type: form.document_type || "CLINICAL_NOTE",
        category: form.category || "GENERAL",
        title: `${form.document_type || "CLINICAL_NOTE"} - ${form.category || "GENERAL"}`,
        content_text: form.content_text || "",
        storage_uri: storageUri || "",
        mime_type: mimeType,
        status: "DRAFT",
        sensitive_flag: false,
        share_sensitivity: "STANDARD"
      });
      setShowModal(false);
      setForm({ category: "GENERAL" });
      setSelectedFile(null);
      load();
    } catch (e: any) { alert("Error: " + e.message); }
    finally { setSaving(false); }
  };

  const handleDelete = async (id: string) => {
    if (!confirm("Are you sure you want to delete this document?")) return;
    try {
      await apiDelete(`/documents/${id}`);
      load();
    } catch (e: any) { alert("Error deleting: " + e.message); }
  };

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setSelectedFile(e.target.files[0]);
    }
  };

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      setSelectedFile(e.dataTransfer.files[0]);
    }
  };

  return (<div><TopNav title="Documents & Records" />
    <div className="p-6 space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div><h2 className="text-lg font-bold text-slate-800">Documents & Records</h2><p className="text-sm text-slate-500">{items.length} records</p></div>
        <button className="btn-primary" onClick={() => setShowModal(true)}>+ Upload Document</button>
      </div>
      {loading ? <div className="flex justify-center py-20"><svg className="w-8 h-8 animate-spin text-teal-600" fill="none" viewBox="0 0 24 24"><circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"/><path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/></svg></div> :
      items.length === 0 ? (
        <div className="text-center py-20">
          <div className="w-20 h-20 mx-auto mb-4 rounded-2xl bg-slate-50 flex items-center justify-center text-4xl">\ud83d\udcc4</div>
          <h3 className="text-lg font-bold text-slate-700">No Documents</h3>
          <p className="text-sm text-slate-500 mt-1">Records will appear here once created</p>
        </div>
      ) :
      <div className="bg-white rounded-2xl border border-slate-200 overflow-hidden shadow-sm overflow-x-auto">
        <table className="data-table min-w-full"><thead><tr><th>#</th><th>Document Type</th><th>Category</th><th>Notes</th><th>Status</th><th>Created</th><th>Actions</th></tr></thead>
          <tbody>{items.map((item: any, i: number) => (
            <tr key={item.document_id || i} className="hover:bg-teal-50/30">
              <td className="text-xs text-slate-400 font-mono">{i + 1}</td>
              <td className="font-semibold text-slate-800">{item.document_type || "—"}</td>
              <td><span className="badge badge-info">{item.category || "—"}</span></td>
              <td className="max-w-xs truncate text-slate-600">{item.content_text || "—"}</td>
              <td><span className="badge badge-info">{item.status || "—"}</span></td>
              <td className="text-xs text-slate-500">{item.created_at ? new Date(item.created_at).toLocaleDateString() : "—"}</td>
              <td className="flex gap-1">
                {item.storage_uri ? (
                  <>
                    <button className="btn-secondary text-xs py-1 px-2" onClick={() => window.open(`${API}/documents/download/${item.storage_uri.split('/').pop()}`, '_blank')}>View</button>
                    <button className="btn-secondary text-xs py-1 px-2" onClick={() => {
                      const link = document.createElement('a');
                      link.href = `${API}/documents/download/${item.storage_uri.split('/').pop()}`;
                      link.download = item.storage_uri.split('/').pop();
                      link.click();
                    }}>Download</button>
                  </>
                ) : (
                  <span className="text-xs text-slate-400">No file</span>
                )}
                <button className="btn-secondary text-xs py-1 px-2 bg-red-100 text-red-700 hover:bg-red-200" onClick={() => handleDelete(item.document_id)}>Delete</button>
              </td>
            </tr>))}</tbody></table>
      </div>}

      {showModal && (
        <div className="modal-overlay" onClick={() => setShowModal(false)}>
          <div className="modal-content" onClick={e => e.stopPropagation()}>
            <div className="modal-header">
              <h3 className="modal-title">New Document</h3>
            </div>
            <div className="modal-body space-y-4">
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">Encounter</label>
                <select className="input-field" value={form.encounter_id || ""} onChange={e => setForm({...form, encounter_id: e.target.value})}>
                  <option value="">Select Encounter</option>
                  {encounters.map((e: any) => (
                    <option key={e.encounter_id} value={e.encounter_id}>
                      {e.patient_name || e.encounter_id.split('-')[0]} - {new Date(e.started_at).toLocaleDateString()}
                    </option>
                  ))}
                </select>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-1">Document Type</label>
                  <select className="input-field" value={form.document_type || "CLINICAL_NOTE"} onChange={e => setForm({...form, document_type: e.target.value})}>
                    <option value="CLINICAL_NOTE">Clinical Note</option>
                    <option value="LAB_REPORT">Lab Report</option>
                    <option value="IMAGING_REPORT">Imaging Report</option>
                    <option value="REFERRAL_LETTER">Referral Letter</option>
                    <option value="SURGICAL_NOTE">Surgical Note</option>
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-1">Category</label>
                  <select className="input-field" value={form.category || "GENERAL"} onChange={e => setForm({...form, category: e.target.value})}>
                    <option value="GENERAL">General</option>
                    <option value="PATIENT">Patient Record</option>
                    <option value="BILLING">Billing</option>
                    <option value="LEGAL">Legal</option>
                    <option value="ADMIN">Administrative</option>
                  </select>
                </div>
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">Notes / Description</label>
                <textarea className="input-field" rows={3} value={form.content_text || ""} onChange={e => setForm({...form, content_text: e.target.value})} placeholder="Add text content or description..."></textarea>
              </div>
              <div
                className={`p-4 border-2 border-dashed rounded-lg text-center cursor-pointer transition-all ${dragActive ? 'border-teal-500 bg-teal-50' : 'border-slate-300 hover:bg-slate-50'}`}
                onDragEnter={handleDrag}
                onDragLeave={handleDrag}
                onDragOver={handleDrag}
                onDrop={handleDrop}
                onClick={() => document.getElementById('fileInput')?.click()}
              >
                <input
                  type="file"
                  id="fileInput"
                  className="hidden"
                  onChange={handleFileSelect}
                />
                {selectedFile ? (
                  <div className="text-slate-700">
                    <p className="font-semibold">{selectedFile.name}</p>
                    <p className="text-xs mt-1">{(selectedFile.size / 1024).toFixed(2)} KB</p>
                  </div>
                ) : (
                  <div className="text-slate-500">
                    <p>Drag and drop file here, or click to browse</p>
                    <p className="text-xs mt-1">Supports PDF, images, and documents</p>
                  </div>
                )}
              </div>
            </div>
            <div className="modal-footer">
              <button type="button" className="btn-secondary" onClick={() => setShowModal(false)} disabled={saving}>Cancel</button>
              <button type="button" className="btn-primary" onClick={handleCreate} disabled={saving || !form.encounter_id}>{saving ? "Saving..." : "Save Document"}</button>
            </div>
          </div>
        </div>
      )}
    </div></div>);
}
