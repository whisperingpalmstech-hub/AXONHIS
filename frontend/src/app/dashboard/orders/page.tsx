"use client";
import { useState, useEffect, useCallback, useRef } from "react";
import { useRouter } from "next/navigation";
import {
  Search, Plus, ClipboardList, FileText, Package, ChevronRight, X, Check,
  AlertTriangle, Clock, Mic, MicOff, Filter, Zap, Activity, Pill,
  Scan, Syringe, Stethoscope, ArrowRight, RotateCcw, CheckCircle2,
  XCircle, Loader2, Volume2, ListOrdered, Layers, ShieldCheck
} from "lucide-react";

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:9500";

const ORDER_TYPES = [
  { value: "LAB_ORDER", label: "Lab Test", icon: Activity, color: "#8B5CF6", bg: "#EDE9FE" },
  { value: "MEDICATION_ORDER", label: "Medication", icon: Pill, color: "#EC4899", bg: "#FCE7F3" },
  { value: "RADIOLOGY_ORDER", label: "Imaging", icon: Scan, color: "#0EA5E9", bg: "#E0F2FE" },
  { value: "PROCEDURE_ORDER", label: "Procedure", icon: Syringe, color: "#F59E0B", bg: "#FEF3C7" },
  { value: "NURSING_TASK", label: "Nursing", icon: Stethoscope, color: "#10B981", bg: "#D1FAE5" },
];

const PRIORITY_MAP: Record<string, { label: string; color: string; bg: string }> = {
  ROUTINE: { label: "Routine", color: "#64748B", bg: "#F1F5F9" },
  URGENT: { label: "Urgent", color: "#F59E0B", bg: "#FEF3C7" },
  STAT: { label: "STAT", color: "#DC2626", bg: "#FEE2E2" },
};

const STATUS_MAP: Record<string, { label: string; color: string; bg: string; icon: any }> = {
  DRAFT: { label: "Draft", color: "#94A3B8", bg: "#F1F5F9", icon: FileText },
  PENDING_APPROVAL: { label: "Pending", color: "#F59E0B", bg: "#FEF3C7", icon: Clock },
  APPROVED: { label: "Approved", color: "#2563EB", bg: "#DBEAFE", icon: CheckCircle2 },
  IN_PROGRESS: { label: "In Progress", color: "#8B5CF6", bg: "#EDE9FE", icon: Loader2 },
  COMPLETED: { label: "Completed", color: "#16A34A", bg: "#DCFCE7", icon: Check },
  CANCELLED: { label: "Cancelled", color: "#DC2626", bg: "#FEE2E2", icon: XCircle },
};

function getHeaders() {
  const token = typeof window !== "undefined" ? localStorage.getItem("access_token") : null;
  return {
    "Content-Type": "application/json",
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
  };
}

// ─── CATALOG SEARCH ITEM COMPONENT ───────────────────────────────────
function CatalogItem({ item, onAdd }: { item: any; onAdd: (item: any) => void }) {
  const typeInfo = ORDER_TYPES.find(o => o.value === item.type);
  return (
    <button
      onClick={() => onAdd(item)}
      className="w-full flex items-center gap-3 px-4 py-3 rounded-lg hover:bg-slate-50 transition-all group text-left border border-transparent hover:border-[var(--border)]"
    >
      <div className="w-8 h-8 rounded-lg flex items-center justify-center text-xs font-bold"
        style={{ background: typeInfo?.bg || "#F1F5F9", color: typeInfo?.color || "#64748B" }}>
        {item.code?.slice(0, 2)}
      </div>
      <div className="flex-1 min-w-0">
        <p className="text-sm font-medium text-[var(--text-primary)] truncate">{item.name}</p>
        <p className="text-xs text-[var(--text-secondary)]">{item.code}</p>
      </div>
      <Plus size={16} className="text-[var(--text-secondary)] opacity-0 group-hover:opacity-100 transition-opacity" />
    </button>
  );
}

// ─── ORDER ITEM BADGE ────────────────────────────────────────────────
function OrderItemBadge({ item, onRemove }: { item: any; onRemove?: () => void }) {
  return (
    <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-[var(--accent-primary-light)] text-[var(--accent-primary)] text-xs font-medium animate-in">
      <span>{item.item_name}</span>
      {onRemove && (
        <button onClick={onRemove} className="hover:text-red-600 transition-colors">
          <X size={12} />
        </button>
      )}
    </div>
  );
}

// ─── CREATE ORDER MODAL ──────────────────────────────────────────────
function CreateOrderModal({
  open, onClose, encounterId, patientId, onCreated
}: {
  open: boolean; onClose: () => void;
  encounterId: string; patientId: string;
  onCreated: () => void;
}) {
  const [step, setStep] = useState(0); // 0=type, 1=items, 2=review
  const [orderType, setOrderType] = useState("");
  const [priority, setPriority] = useState("ROUTINE");
  const [notes, setNotes] = useState("");
  const [items, setItems] = useState<any[]>([]);
  const [searchQ, setSearchQ] = useState("");
  const [catalogResults, setCatalogResults] = useState<any[]>([]);
  const [searching, setSearching] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [isListening, setIsListening] = useState(false);
  const recognitionRef = useRef<any>(null);
  const searchTimerRef = useRef<any>(null);

  // Catalog search with debounce — searches ALL types so user sees full catalog
  useEffect(() => {
    if (searchQ.length < 2) { setCatalogResults([]); return; }
    if (searchTimerRef.current) clearTimeout(searchTimerRef.current);
    searchTimerRef.current = setTimeout(async () => {
      setSearching(true);
      try {
        const res = await fetch(`${API}/api/v1/orders/catalog/search?q=${encodeURIComponent(searchQ)}`, { headers: getHeaders() });
        if (res.ok) setCatalogResults(await res.json());
      } catch { /* ignore */ }
      setSearching(false);
    }, 300);
    return () => { if (searchTimerRef.current) clearTimeout(searchTimerRef.current); };
  }, [searchQ]);

  // Voice input
  const toggleVoice = () => {
    if (!("webkitSpeechRecognition" in window || "SpeechRecognition" in window)) {
      alert("Speech recognition not supported in this browser");
      return;
    }
    if (isListening) {
      recognitionRef.current?.stop();
      setIsListening(false);
      return;
    }
    const SpeechRecognition = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
    const recognition = new SpeechRecognition();
    recognition.continuous = false;
    recognition.interimResults = false;
    recognition.lang = "en-US";
    recognition.onresult = (e: any) => {
      const transcript = e.results[0][0].transcript;
      setSearchQ(transcript);
    };
    recognition.onend = () => setIsListening(false);
    recognition.onerror = () => setIsListening(false);
    recognitionRef.current = recognition;
    recognition.start();
    setIsListening(true);
  };

  const addItem = (catalogItem: any) => {
    if (items.find(i => i.item_name === catalogItem.name)) return;
    setItems(prev => [...prev, {
      item_type: catalogItem.type === "MEDICATION_ORDER" ? "medication" : catalogItem.type === "LAB_ORDER" ? "lab_test" : "procedure",
      item_name: catalogItem.name,
      item_code: catalogItem.code,
      quantity: 1, unit_price: 0, instructions: "",
    }]);
    // Auto-set order type from the first item added, or update if different
    if (!orderType || items.length === 0) setOrderType(catalogItem.type);
  };

  const removeItem = (idx: number) => setItems(prev => prev.filter((_, i) => i !== idx));

  const submit = async () => {
    setSubmitting(true);
    try {
      const res = await fetch(`${API}/api/v1/orders`, {
        method: "POST", headers: getHeaders(),
        body: JSON.stringify({
          encounter_id: encounterId,
          patient_id: patientId,
          order_type: orderType,
          priority, notes,
          metadata_: {},
          items: items.map(i => ({
            item_type: i.item_type, item_name: i.item_name,
            quantity: i.quantity, unit_price: i.unit_price,
            instructions: i.instructions,
          })),
        }),
      });
      if (res.ok) { onCreated(); onClose(); resetForm(); }
      else { const e = await res.json(); alert(e.detail || "Failed to create order"); }
    } catch (err) { alert("Network error"); }
    setSubmitting(false);
  };

  const resetForm = () => {
    setStep(0); setOrderType(""); setPriority("ROUTINE");
    setNotes(""); setItems([]); setSearchQ(""); setCatalogResults([]);
  };

  if (!open) return null;

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="bg-white rounded-2xl shadow-2xl w-full max-w-2xl mx-4 max-h-[90vh] overflow-hidden flex flex-col"
        onClick={e => e.stopPropagation()}
        style={{ animation: "slideUp 0.3s ease-out" }}>

        {/* Header */}
        <div className="px-6 py-4 border-b border-[var(--border)] flex items-center justify-between bg-gradient-to-r from-[var(--accent-primary)] to-[#7C3AED]">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-white/20 rounded-xl flex items-center justify-center backdrop-blur-sm">
              <ClipboardList size={20} className="text-white" />
            </div>
            <div>
              <h3 className="text-lg font-semibold text-white">New Order</h3>
              <p className="text-xs text-white/70">Step {step + 1} of 3</p>
            </div>
          </div>
          <button onClick={() => { onClose(); resetForm(); }} className="text-white/70 hover:text-white transition-colors">
            <X size={20} />
          </button>
        </div>

        {/* Progress bar */}
        <div className="h-1 bg-slate-100">
          <div className="h-full bg-gradient-to-r from-[var(--accent-primary)] to-[#7C3AED] transition-all duration-500"
            style={{ width: `${((step + 1) / 3) * 100}%` }} />
        </div>

        {/* Body */}
        <div className="flex-1 overflow-y-auto p-6">

          {/* Step 0: Order Type */}
          {step === 0 && (
            <div className="space-y-5">
              <div>
                <h4 className="text-base font-semibold mb-1">Select Order Type</h4>
                <p className="text-sm text-[var(--text-secondary)]">Choose the category for this clinical order</p>
              </div>
              <div className="grid grid-cols-2 gap-3">
                {ORDER_TYPES.map(type => {
                  const Icon = type.icon;
                  const selected = orderType === type.value;
                  return (
                    <button key={type.value}
                      onClick={() => setOrderType(type.value)}
                      className={`p-4 rounded-xl border-2 transition-all text-left group ${
                        selected ? "border-[var(--accent-primary)] bg-[var(--accent-primary-light)] shadow-md" : "border-[var(--border)] hover:border-slate-300 hover:shadow-sm"}`}>
                      <div className="flex items-center gap-3">
                        <div className="w-10 h-10 rounded-xl flex items-center justify-center"
                          style={{ background: type.bg, color: type.color }}>
                          <Icon size={20} />
                        </div>
                        <span className={`font-medium text-sm ${selected ? "text-[var(--accent-primary)]" : "text-[var(--text-primary)]"}`}>
                          {type.label}
                        </span>
                      </div>
                    </button>
                  );
                })}
              </div>

              {/* Priority */}
              <div>
                <label className="input-label">Priority</label>
                <div className="flex gap-2">
                  {Object.entries(PRIORITY_MAP).map(([key, val]) => (
                    <button key={key}
                      onClick={() => setPriority(key)}
                      className={`px-4 py-2 rounded-lg text-sm font-medium transition-all ${
                        priority === key ? "ring-2 ring-offset-1 shadow-sm" : "hover:opacity-80"}`}
                      style={{ background: val.bg, color: val.color, ...(priority === key ? { ringColor: val.color } : {}) }}>
                      {key === "STAT" && <Zap size={12} className="inline mr-1" />}
                      {val.label}
                    </button>
                  ))}
                </div>
              </div>
            </div>
          )}

          {/* Step 1: Add Items */}
          {step === 1 && (
            <div className="space-y-4">
              <div>
                <h4 className="text-base font-semibold mb-1">Add Order Items</h4>
                <p className="text-sm text-[var(--text-secondary)]">Search or use voice to add tests, medications, or procedures</p>
              </div>

              {/* Search bar with voice */}
              <div className="relative">
                <Search size={18} className="absolute left-3.5 top-1/2 -translate-y-1/2 text-[var(--text-secondary)]" />
                <input
                  value={searchQ}
                  onChange={e => setSearchQ(e.target.value)}
                  placeholder='Search "CBC", "Aspirin", "ECG"...'
                  className="input-field pl-10 pr-12"
                  autoFocus
                />
                <button onClick={toggleVoice}
                  className={`absolute right-2 top-1/2 -translate-y-1/2 p-2 rounded-lg transition-all ${
                    isListening ? "bg-red-100 text-red-600 animate-pulse" : "text-[var(--text-secondary)] hover:bg-slate-100"}`}>
                  {isListening ? <MicOff size={16} /> : <Mic size={16} />}
                </button>
              </div>

              {/* Search results */}
              {searching && (
                <div className="flex items-center gap-2 text-sm text-[var(--text-secondary)] p-3">
                  <Loader2 size={14} className="animate-spin" />Searching catalog...
                </div>
              )}
              {catalogResults.length > 0 && (
                <div className="border border-[var(--border)] rounded-xl max-h-48 overflow-y-auto divide-y divide-[var(--border)]">
                  {catalogResults.map((item, i) => (
                    <CatalogItem key={i} item={item} onAdd={addItem} />
                  ))}
                </div>
              )}

              {/* Selected items */}
              {items.length > 0 && (
                <div>
                  <label className="input-label">Selected Items ({items.length})</label>
                  <div className="space-y-2">
                    {items.map((item, i) => (
                      <div key={i} className="flex items-center gap-3 p-3 rounded-lg bg-slate-50 border border-[var(--border)]">
                        <div className="flex-1">
                          <p className="text-sm font-medium">{item.item_name}</p>
                          <input
                            placeholder="Special instructions..."
                            value={item.instructions}
                            onChange={e => {
                              const updated = [...items];
                              updated[i].instructions = e.target.value;
                              setItems(updated);
                            }}
                            className="mt-1 w-full px-2 py-1 text-xs rounded border border-[var(--border)] bg-white focus:outline-none focus:ring-1 focus:ring-[var(--accent-primary)]"
                          />
                        </div>
                        <div className="flex items-center gap-2">
                          <label className="text-xs text-[var(--text-secondary)]">Qty</label>
                          <input type="number" min="1" value={item.quantity}
                            onChange={e => {
                              const updated = [...items];
                              updated[i].quantity = Number(e.target.value) || 1;
                              setItems(updated);
                            }}
                            className="w-14 px-2 py-1 text-xs rounded border border-[var(--border)] text-center" />
                        </div>
                        <button onClick={() => removeItem(i)} className="text-red-400 hover:text-red-600 transition-colors p-1">
                          <X size={14} />
                        </button>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Notes */}
              <div>
                <label className="input-label">Clinical Notes (Optional)</label>
                <textarea
                  value={notes} onChange={e => setNotes(e.target.value)}
                  placeholder="Additional instructions or clinical context..."
                  className="input-field h-20 resize-none"
                />
              </div>
            </div>
          )}

          {/* Step 2: Review */}
          {step === 2 && (
            <div className="space-y-5">
              <div>
                <h4 className="text-base font-semibold mb-1">Review Order</h4>
                <p className="text-sm text-[var(--text-secondary)]">Confirm details before submission</p>
              </div>

              {/* Order type & priority */}
              <div className="grid grid-cols-2 gap-4">
                <div className="p-4 rounded-xl bg-slate-50 border border-[var(--border)]">
                  <p className="text-xs text-[var(--text-secondary)] mb-1">Order Type</p>
                  <p className="font-semibold text-sm">{ORDER_TYPES.find(t => t.value === orderType)?.label}</p>
                </div>
                <div className="p-4 rounded-xl bg-slate-50 border border-[var(--border)]">
                  <p className="text-xs text-[var(--text-secondary)] mb-1">Priority</p>
                  <span className="px-2.5 py-1 rounded-full text-xs font-medium"
                    style={{ background: PRIORITY_MAP[priority]?.bg, color: PRIORITY_MAP[priority]?.color }}>
                    {PRIORITY_MAP[priority]?.label}
                  </span>
                </div>
              </div>

              {/* Items list */}
              <div>
                <p className="text-xs text-[var(--text-secondary)] mb-2 font-medium uppercase tracking-wider">Order Items</p>
                <div className="space-y-2">
                  {items.map((item, i) => (
                    <div key={i} className="flex items-center gap-3 p-3 rounded-lg bg-white border border-[var(--border)]">
                      <CheckCircle2 size={16} className="text-green-500 shrink-0" />
                      <div className="flex-1">
                        <p className="text-sm font-medium">{item.item_name}</p>
                        {item.instructions && <p className="text-xs text-[var(--text-secondary)] mt-0.5">{item.instructions}</p>}
                      </div>
                      <span className="text-xs text-[var(--text-secondary)]">×{item.quantity}</span>
                    </div>
                  ))}
                </div>
              </div>

              {/* Notes */}
              {notes && (
                <div className="p-4 rounded-xl bg-amber-50 border border-amber-200">
                  <p className="text-xs text-amber-800 font-medium mb-1">Clinical Notes</p>
                  <p className="text-sm text-amber-900">{notes}</p>
                </div>
              )}

              <div className="p-3 rounded-lg bg-blue-50 border border-blue-200 flex items-center gap-2">
                <ShieldCheck size={16} className="text-blue-600" />
                <p className="text-xs text-blue-800">This order will be sent for approval after submission.</p>
              </div>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="px-6 py-4 border-t border-[var(--border)] flex items-center justify-between bg-slate-50">
          {step > 0 ? (
            <button onClick={() => setStep(s => s - 1)} className="btn-secondary btn-sm">
              Back
            </button>
          ) : <div />}
          <div className="flex gap-2">
            <button onClick={() => { onClose(); resetForm(); }} className="btn-secondary btn-sm">Cancel</button>
            {step < 2 ? (
              <button
                onClick={() => setStep(s => s + 1)}
                disabled={step === 0 ? !orderType : items.length === 0}
                className="btn-primary btn-sm">
                Next <ChevronRight size={14} />
              </button>
            ) : (
              <button onClick={submit} disabled={submitting} className="btn-primary btn-sm">
                {submitting ? <><Loader2 size={14} className="animate-spin" />Submitting...</> : <><Check size={14} />Submit Order</>}
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}


// ─── MAIN ORDERS PAGE ────────────────────────────────────────────────
export default function OrdersPage() {
  const router = useRouter();
  const [orders, setOrders] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [showCreate, setShowCreate] = useState(false);
  const [filterType, setFilterType] = useState("");
  const [filterStatus, setFilterStatus] = useState("");
  const [encounters, setEncounters] = useState<any[]>([]);
  const [selectedEncounter, setSelectedEncounter] = useState<any>(null);
  const [showEncounterPicker, setShowEncounterPicker] = useState(false);
  const [templates, setTemplates] = useState<any[]>([]);
  const [orderSets, setOrderSets] = useState<any[]>([]);
  const [activeTab, setActiveTab] = useState<"orders" | "templates" | "sets">("orders");
  const [actionLoading, setActionLoading] = useState<string | null>(null);

  // Template creation
  const [showCreateTemplate, setShowCreateTemplate] = useState(false);
  const [tplForm, setTplForm] = useState<any>({ name: "", desc: "", type: "", items: [] });
  const [tplSearch, setTplSearch] = useState("");
  const [tplCatalog, setTplCatalog] = useState<any[]>([]);

  // Order Set creation
  const [showCreateSet, setShowCreateSet] = useState(false);
  const [setForm, setSetForm] = useState<any>({ name: "", desc: "", context: "", items: [] });
  const [setSearch, setSetSearch] = useState("");
  const [setCatalog, setSetCatalog] = useState<any[]>([]);

  // Catalog search helper (reusable)
  const searchCatalogFor = async (q: string, setter: (r: any[]) => void) => {
    if (q.length < 2) { setter([]); return; }
    try {
      const res = await fetch(`${API}/api/v1/orders/catalog/search?q=${encodeURIComponent(q)}`, { headers: getHeaders() });
      if (res.ok) setter(await res.json());
    } catch { /* ignore */ }
  };

  // Submit template
  const submitTemplate = async () => {
    try {
      const res = await fetch(`${API}/api/v1/orders/order-templates`, {
        method: "POST", headers: getHeaders(),
        body: JSON.stringify({
          template_name: tplForm.name,
          description: tplForm.desc,
          order_type: tplForm.type,
          items: tplForm.items.map((i: any) => ({ item_type: i.item_type, item_name: i.item_name, item_code: i.item_code, default_quantity: 1 })),
        }),
      });
      if (res.ok) {
        setShowCreateTemplate(false);
        setTplForm({ name: "", desc: "", type: "", items: [] });
        loadTemplates();
      } else { const e = await res.json(); alert(e.detail || "Failed"); }
    } catch { alert("Network error"); }
  };

  // Submit order set
  const submitOrderSet = async () => {
    try {
      const res = await fetch(`${API}/api/v1/orders/order-sets`, {
        method: "POST", headers: getHeaders(),
        body: JSON.stringify({
          set_name: setForm.name,
          description: setForm.desc,
          clinical_context: setForm.context || null,
          items: setForm.items.map((i: any, idx: number) => ({
            order_type: i.order_type, item_name: i.item_name, item_code: i.item_code,
            default_quantity: 1, sort_order: idx,
          })),
        }),
      });
      if (res.ok) {
        setShowCreateSet(false);
        setSetForm({ name: "", desc: "", context: "", items: [] });
        loadOrderSets();
      } else { const e = await res.json(); alert(e.detail || "Failed"); }
    } catch { alert("Network error"); }
  };

  // Load active encounters to pick from
  const loadEncounters = useCallback(async () => {
    try {
      const res = await fetch(`${API}/api/v1/encounters/?status=active&limit=50`, { headers: getHeaders() });
      if (res.ok) setEncounters(await res.json());
    } catch { /* ignore */ }
  }, []);

  // Load orders for a specific encounter
  const loadOrders = useCallback(async (encId: string) => {
    setLoading(true);
    try {
      const res = await fetch(`${API}/api/v1/orders/encounter/${encId}`, { headers: getHeaders() });
      if (res.ok) setOrders(await res.json());
    } catch { /* ignore */ }
    setLoading(false);
  }, []);

  // Load templates
  const loadTemplates = useCallback(async () => {
    try {
      const res = await fetch(`${API}/api/v1/orders/order-templates`, { headers: getHeaders() });
      if (res.ok) setTemplates(await res.json());
    } catch { /* ignore */ }
  }, []);

  // Load order sets
  const loadOrderSets = useCallback(async () => {
    try {
      const res = await fetch(`${API}/api/v1/orders/order-sets`, { headers: getHeaders() });
      if (res.ok) setOrderSets(await res.json());
    } catch { /* ignore */ }
  }, []);

  useEffect(() => { loadEncounters(); loadTemplates(); loadOrderSets(); }, []);

  useEffect(() => {
    if (selectedEncounter) loadOrders(selectedEncounter.id);
    else setLoading(false);
  }, [selectedEncounter]);

  // Approve order
  const approveOrder = async (orderId: string) => {
    setActionLoading(orderId);
    try {
      const res = await fetch(`${API}/api/v1/orders/${orderId}/approve`, {
        method: "POST", headers: getHeaders(),
        body: JSON.stringify({ notes: null }),
      });
      if (res.ok && selectedEncounter) loadOrders(selectedEncounter.id);
      else { const e = await res.json(); alert(e.detail || "Approval failed"); }
    } catch { alert("Network error"); }
    setActionLoading(null);
  };

  // Cancel order
  const cancelOrder = async (orderId: string) => {
    const reason = prompt("Enter cancellation reason:");
    if (!reason || reason.length < 5) { alert("Reason must be at least 5 characters"); return; }
    setActionLoading(orderId);
    try {
      const res = await fetch(`${API}/api/v1/orders/${orderId}/cancel`, {
        method: "POST", headers: getHeaders(),
        body: JSON.stringify({ reason }),
      });
      if (res.ok && selectedEncounter) loadOrders(selectedEncounter.id);
      else { const e = await res.json(); alert(e.detail || "Cancellation failed"); }
    } catch { alert("Network error"); }
    setActionLoading(null);
  };

  // Filtered orders
  const filtered = orders.filter(o => {
    if (filterType && o.order_type !== filterType) return false;
    if (filterStatus && o.status !== filterStatus) return false;
    return true;
  });

  return (
    <div className="min-h-screen bg-[var(--bg-primary)]">
      {/* Top bar */}
      <div className="topnav">
        <div className="flex items-center gap-4">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-[var(--accent-primary)] to-[#7C3AED] flex items-center justify-center">
            <ClipboardList size={20} className="text-white" />
          </div>
          <div>
            <h1 className="text-lg font-bold">Order Management</h1>
            <p className="text-xs text-[var(--text-secondary)]">Phase 4 — Enterprise Order Engine</p>
          </div>
        </div>
        <div className="flex items-center gap-3">
          {selectedEncounter && (
            <button onClick={() => setShowCreate(true)} className="btn-primary btn-sm">
              <Plus size={14} /> New Order
            </button>
          )}
        </div>
      </div>

      <div className="p-6 space-y-6">

        {/* Encounter Selector */}
        <div className="card card-body">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 rounded-lg bg-[var(--accent-primary-light)] flex items-center justify-center">
                <FileText size={16} className="text-[var(--accent-primary)]" />
              </div>
              <div>
                <p className="text-sm font-semibold">
                  {selectedEncounter ? `Encounter: ${selectedEncounter.encounter_type || "Visit"} — ${selectedEncounter.department || "General"}` : "Select an Encounter"}
                </p>
                <p className="text-xs text-[var(--text-secondary)]">
                  {selectedEncounter ? `Patient: ${selectedEncounter.patient_id?.slice(0, 8)}...` : "Choose an active encounter to manage orders"}
                </p>
              </div>
            </div>
            <button onClick={() => setShowEncounterPicker(true)} className="btn-secondary btn-sm">
              {selectedEncounter ? "Change" : "Select Encounter"}
            </button>
          </div>
        </div>

        {/* Tabs */}
        <div className="flex gap-1 bg-slate-100 p-1 rounded-xl w-fit">
          {[
            { key: "orders" as const, label: "Orders", icon: ListOrdered },
            { key: "templates" as const, label: "Templates", icon: Layers },
            { key: "sets" as const, label: "Order Sets", icon: Package },
          ].map(tab => {
            const Icon = tab.icon;
            return (
              <button key={tab.key}
                onClick={() => setActiveTab(tab.key)}
                className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all ${
                  activeTab === tab.key ? "bg-white shadow-sm text-[var(--accent-primary)]" : "text-[var(--text-secondary)] hover:text-[var(--text-primary)]"}`}>
                <Icon size={14} /> {tab.label}
              </button>
            );
          })}
        </div>

        {/* Orders Tab */}
        {activeTab === "orders" && (
          <>
            {!selectedEncounter ? (
              <div className="card card-body text-center py-16">
                <div className="w-20 h-20 mx-auto mb-4 rounded-2xl bg-slate-100 flex items-center justify-center">
                  <ClipboardList size={32} className="text-slate-400" />
                </div>
                <h3 className="text-lg font-semibold mb-2">No Encounter Selected</h3>
                <p className="text-sm text-[var(--text-secondary)] mb-4">Select an active encounter to view and manage clinical orders</p>
                <button onClick={() => setShowEncounterPicker(true)} className="btn-primary">
                  <FileText size={14} /> Select Encounter
                </button>
              </div>
            ) : (
              <>
                {/* Filters */}
                <div className="flex gap-3 items-center flex-wrap">
                  <div className="flex items-center gap-2 text-sm text-[var(--text-secondary)]">
                    <Filter size={14} /> Filter:
                  </div>
                  <select value={filterType} onChange={e => setFilterType(e.target.value)}
                    className="px-3 py-1.5 rounded-lg border border-[var(--border)] text-sm bg-white">
                    <option value="">All Types</option>
                    {ORDER_TYPES.map(t => <option key={t.value} value={t.value}>{t.label}</option>)}
                  </select>
                  <select value={filterStatus} onChange={e => setFilterStatus(e.target.value)}
                    className="px-3 py-1.5 rounded-lg border border-[var(--border)] text-sm bg-white">
                    <option value="">All Statuses</option>
                    {Object.entries(STATUS_MAP).map(([k, v]) => <option key={k} value={k}>{v.label}</option>)}
                  </select>
                  <span className="text-xs text-[var(--text-secondary)]">{filtered.length} order{filtered.length !== 1 ? "s" : ""}</span>
                </div>

                {/* Orders List */}
                {loading ? (
                  <div className="card card-body text-center py-12">
                    <Loader2 size={24} className="animate-spin mx-auto text-[var(--accent-primary)]" />
                    <p className="text-sm text-[var(--text-secondary)] mt-3">Loading orders...</p>
                  </div>
                ) : filtered.length === 0 ? (
                  <div className="card card-body text-center py-12">
                    <Package size={32} className="mx-auto text-slate-300 mb-3" />
                    <p className="text-sm text-[var(--text-secondary)]">No orders found. Create the first order for this encounter.</p>
                  </div>
                ) : (
                  <div className="space-y-3">
                    {filtered.map(order => {
                      const typeInfo = ORDER_TYPES.find(t => t.value === order.order_type);
                      const statusInfo = STATUS_MAP[order.status] || STATUS_MAP.DRAFT;
                      const priorityInfo = PRIORITY_MAP[order.priority] || PRIORITY_MAP.ROUTINE;
                      const TypeIcon = typeInfo?.icon || ClipboardList;
                      const StatusIcon = statusInfo.icon;
                      return (
                        <div key={order.id} className="card overflow-hidden hover:shadow-md transition-shadow">
                          <div className="flex items-stretch">
                            {/* Left color strip */}
                            <div className="w-1.5" style={{ background: typeInfo?.color || "#94A3B8" }} />

                            <div className="flex-1 p-4">
                              <div className="flex items-start justify-between gap-4">
                                <div className="flex items-start gap-3">
                                  <div className="w-10 h-10 rounded-xl flex items-center justify-center shrink-0"
                                    style={{ background: typeInfo?.bg || "#F1F5F9", color: typeInfo?.color || "#64748B" }}>
                                    <TypeIcon size={18} />
                                  </div>
                                  <div>
                                    <p className="font-semibold text-sm">{typeInfo?.label || order.order_type}</p>
                                    <div className="flex items-center gap-2 mt-1 flex-wrap">
                                      <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium"
                                        style={{ background: statusInfo.bg, color: statusInfo.color }}>
                                        <StatusIcon size={10} /> {statusInfo.label}
                                      </span>
                                      <span className="px-2 py-0.5 rounded-full text-xs font-medium"
                                        style={{ background: priorityInfo.bg, color: priorityInfo.color }}>
                                        {priorityInfo.label}
                                      </span>
                                      <span className="text-xs text-[var(--text-secondary)]">
                                        {new Date(order.created_at).toLocaleString()}
                                      </span>
                                    </div>
                                    {/* Items */}
                                    {order.items?.length > 0 && (
                                      <div className="flex flex-wrap gap-1.5 mt-2">
                                        {order.items.map((item: any, i: number) => (
                                          <OrderItemBadge key={i} item={item} />
                                        ))}
                                      </div>
                                    )}
                                    {order.notes && (
                                      <p className="text-xs text-[var(--text-secondary)] mt-2 italic">📝 {order.notes}</p>
                                    )}
                                  </div>
                                </div>

                                {/* Actions */}
                                <div className="flex items-center gap-2 shrink-0">
                                  {order.status === "PENDING_APPROVAL" && (
                                    <>
                                      <button onClick={() => approveOrder(order.id)}
                                        disabled={actionLoading === order.id}
                                        className="btn-sm px-3 py-1.5 rounded-lg bg-green-50 text-green-700 hover:bg-green-100 text-xs font-medium transition-colors inline-flex items-center gap-1">
                                        {actionLoading === order.id ? <Loader2 size={12} className="animate-spin" /> : <Check size={12} />}
                                        Approve
                                      </button>
                                      <button onClick={() => cancelOrder(order.id)}
                                        disabled={actionLoading === order.id}
                                        className="btn-sm px-3 py-1.5 rounded-lg bg-red-50 text-red-700 hover:bg-red-100 text-xs font-medium transition-colors inline-flex items-center gap-1">
                                        <XCircle size={12} /> Cancel
                                      </button>
                                    </>
                                  )}
                                  {(order.status === "APPROVED" || order.status === "IN_PROGRESS") && (
                                    <button onClick={() => cancelOrder(order.id)}
                                      disabled={actionLoading === order.id}
                                      className="btn-sm px-3 py-1.5 rounded-lg bg-red-50 text-red-700 hover:bg-red-100 text-xs font-medium transition-colors inline-flex items-center gap-1">
                                      <XCircle size={12} /> Cancel
                                    </button>
                                  )}
                                </div>
                              </div>
                            </div>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                )}
              </>
            )}
          </>
        )}

        {/* Templates Tab */}
        {activeTab === "templates" && (
          <div className="space-y-5">
            {/* Header bar */}
            <div className="flex items-center justify-between">
              <div>
                <h3 className="font-semibold text-base">Order Templates</h3>
                <p className="text-xs text-[var(--text-secondary)]">Reusable order combinations for fast clinical ordering</p>
              </div>
              <button onClick={() => setShowCreateTemplate(true)} className="btn-primary btn-sm">
                <Plus size={14} /> New Template
              </button>
            </div>

            {templates.length === 0 ? (
              <div className="card overflow-hidden">
                <div className="relative py-16 px-8 text-center">
                  <div className="absolute inset-0 bg-gradient-to-br from-purple-50 via-white to-blue-50 opacity-70" />
                  <div className="relative">
                    <div className="w-20 h-20 mx-auto mb-5 rounded-2xl bg-gradient-to-br from-purple-500 to-blue-500 flex items-center justify-center shadow-lg shadow-purple-200">
                      <Layers size={32} className="text-white" />
                    </div>
                    <h3 className="text-lg font-bold mb-2">Create Your First Template</h3>
                    <p className="text-sm text-[var(--text-secondary)] max-w-md mx-auto mb-5">
                      Templates save time during clinical ordering. Create reusable order combinations
                      like &quot;Pneumonia Workup&quot; or &quot;Diabetic Panel&quot; with pre-defined items.
                    </p>
                    <div className="flex items-center justify-center gap-6 mb-6">
                      {[
                        { icon: Activity, label: "Lab Panels", color: "#8B5CF6" },
                        { icon: Pill, label: "Med Protocols", color: "#EC4899" },
                        { icon: Scan, label: "Imaging Sets", color: "#0EA5E9" },
                      ].map((item, i) => {
                        const Icon = item.icon;
                        return (
                          <div key={i} className="flex flex-col items-center gap-1.5">
                            <div className="w-12 h-12 rounded-xl flex items-center justify-center bg-white shadow-sm border border-[var(--border)]">
                              <Icon size={20} style={{ color: item.color }} />
                            </div>
                            <span className="text-xs text-[var(--text-secondary)]">{item.label}</span>
                          </div>
                        );
                      })}
                    </div>
                    <button onClick={() => setShowCreateTemplate(true)} className="btn-primary">
                      <Plus size={14} /> Create Template
                    </button>
                  </div>
                </div>
              </div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {templates.map((tpl: any) => {
                  const typeInfo = ORDER_TYPES.find(t => t.value === tpl.order_type);
                  const TypeIcon = typeInfo?.icon || FileText;
                  return (
                    <div key={tpl.id} className="card hover:shadow-lg transition-all cursor-pointer group overflow-hidden">
                      {/* Top color gradient bar */}
                      <div className="h-1.5 w-full" style={{ background: `linear-gradient(to right, ${typeInfo?.color || "#94A3B8"}, ${typeInfo?.color || "#94A3B8"}88)` }} />
                      <div className="p-5">
                        <div className="flex items-start justify-between mb-3">
                          <div className="w-11 h-11 rounded-xl flex items-center justify-center shadow-sm"
                            style={{ background: typeInfo?.bg || "#F1F5F9", color: typeInfo?.color || "#64748B" }}>
                            <TypeIcon size={20} />
                          </div>
                          <div className="flex items-center gap-2">
                            <span className="px-2 py-0.5 rounded-full text-[10px] font-semibold uppercase tracking-wider"
                              style={{ background: typeInfo?.bg, color: typeInfo?.color }}>
                              {typeInfo?.label}
                            </span>
                          </div>
                        </div>
                        <h4 className="font-bold text-sm mb-1 group-hover:text-[var(--accent-primary)] transition-colors">{tpl.template_name}</h4>
                        <p className="text-xs text-[var(--text-secondary)] mb-3 line-clamp-2">{tpl.description || "No description"}</p>
                        <div className="flex items-center gap-2 mb-3">
                          <div className="flex items-center gap-1 text-xs text-[var(--text-secondary)]">
                            <ListOrdered size={12} />
                            <span>{tpl.items?.length || 0} items</span>
                          </div>
                          <span className="text-slate-300">·</span>
                          <span className="text-xs text-[var(--text-secondary)]">
                            {new Date(tpl.created_at).toLocaleDateString()}
                          </span>
                        </div>
                        <div className="flex flex-wrap gap-1.5">
                          {tpl.items?.slice(0, 4).map((item: any, i: number) => (
                            <span key={i} className="px-2 py-0.5 rounded-md bg-slate-50 border border-slate-100 text-[11px] text-slate-600 font-medium">
                              {item.item_name}
                            </span>
                          ))}
                          {tpl.items?.length > 4 && (
                            <span className="px-2 py-0.5 rounded-md bg-slate-50 text-[11px] text-slate-500">
                              +{tpl.items.length - 4} more
                            </span>
                          )}
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        )}

        {/* Order Sets Tab */}
        {activeTab === "sets" && (
          <div className="space-y-5">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="font-semibold text-base">Order Sets</h3>
                <p className="text-xs text-[var(--text-secondary)]">Multi-domain order bundles for clinical protocols</p>
              </div>
              <button onClick={() => setShowCreateSet(true)} className="btn-primary btn-sm">
                <Plus size={14} /> New Order Set
              </button>
            </div>

            {orderSets.length === 0 ? (
              <div className="card overflow-hidden">
                <div className="relative py-16 px-8 text-center">
                  <div className="absolute inset-0 bg-gradient-to-br from-sky-50 via-white to-emerald-50 opacity-70" />
                  <div className="relative">
                    <div className="w-20 h-20 mx-auto mb-5 rounded-2xl bg-gradient-to-br from-sky-500 to-emerald-500 flex items-center justify-center shadow-lg shadow-sky-200">
                      <Package size={32} className="text-white" />
                    </div>
                    <h3 className="text-lg font-bold mb-2">Create Your First Order Set</h3>
                    <p className="text-sm text-[var(--text-secondary)] max-w-md mx-auto mb-5">
                      Order sets bundle multiple orders across different domains.
                      Perfect for clinical protocols like &quot;ER Chest Pain&quot; or &quot;Sepsis Bundle&quot;.
                    </p>
                    <div className="flex items-center justify-center gap-3 mb-6">
                      {ORDER_TYPES.slice(0, 4).map((type, i) => {
                        const Icon = type.icon;
                        return (
                          <div key={i} className="w-10 h-10 rounded-xl flex items-center justify-center bg-white shadow-sm border border-[var(--border)]"
                            style={{ color: type.color }}>
                            <Icon size={18} />
                          </div>
                        );
                      })}
                      <div className="flex items-center gap-0.5 text-slate-400">
                        <ArrowRight size={14} />
                        <span className="text-xs font-medium">Combined</span>
                      </div>
                    </div>
                    <button onClick={() => setShowCreateSet(true)} className="btn-primary">
                      <Plus size={14} /> Create Order Set
                    </button>
                  </div>
                </div>
              </div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {orderSets.map((set: any) => {
                  const uniqueTypes = [...new Set(set.items?.map((i: any) => i.order_type) || [])];
                  return (
                    <div key={set.id} className="card hover:shadow-lg transition-all overflow-hidden group">
                      {/* Multi-color top bar */}
                      <div className="h-1.5 w-full flex">
                        {uniqueTypes.map((t: string, i: number) => {
                          const info = ORDER_TYPES.find(o => o.value === t);
                          return <div key={i} className="flex-1" style={{ background: info?.color || "#94A3B8" }} />;
                        })}
                      </div>
                      <div className="p-5">
                        <div className="flex items-start justify-between mb-3">
                          <div>
                            <h4 className="font-bold text-sm group-hover:text-[var(--accent-primary)] transition-colors">{set.set_name}</h4>
                            <p className="text-xs text-[var(--text-secondary)] mt-0.5">{set.description || "Multi-domain order set"}</p>
                          </div>
                          {set.clinical_context && (
                            <span className="px-2.5 py-1 rounded-lg text-[10px] font-bold uppercase tracking-wider bg-gradient-to-r from-sky-50 to-sky-100 text-sky-700 border border-sky-200">
                              {set.clinical_context}
                            </span>
                          )}
                        </div>
                        {/* Type summary icons */}
                        <div className="flex items-center gap-2 mb-3">
                          {uniqueTypes.map((t: string, i: number) => {
                            const info = ORDER_TYPES.find(o => o.value === t);
                            const Icon = info?.icon || Zap;
                            const count = set.items?.filter((it: any) => it.order_type === t).length;
                            return (
                              <div key={i} className="flex items-center gap-1 px-2 py-1 rounded-md bg-slate-50 border border-slate-100">
                                <Icon size={12} style={{ color: info?.color }} />
                                <span className="text-[10px] font-semibold" style={{ color: info?.color }}>{count}</span>
                              </div>
                            );
                          })}
                          <span className="text-xs text-[var(--text-secondary)] ml-auto">{set.items?.length} items total</span>
                        </div>
                        {/* Items list */}
                        <div className="space-y-1">
                          {set.items?.map((item: any, i: number) => {
                            const itemType = ORDER_TYPES.find(t => t.value === item.order_type);
                            const Icon = itemType?.icon || Zap;
                            return (
                              <div key={i} className="flex items-center gap-2 px-3 py-2 rounded-lg bg-slate-50/80 hover:bg-slate-100 transition-colors">
                                <div className="w-6 h-6 rounded-md flex items-center justify-center"
                                  style={{ background: itemType?.bg || "#F1F5F9", color: itemType?.color || "#64748B" }}>
                                  <Icon size={12} />
                                </div>
                                <span className="text-xs font-medium flex-1">{item.item_name}</span>
                                <span className="text-[10px] text-[var(--text-secondary)] px-1.5 py-0.5 rounded bg-white border border-slate-100">
                                  {itemType?.label}
                                </span>
                              </div>
                            );
                          })}
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        )}
      </div>

      {/* Encounter picker modal */}
      {showEncounterPicker && (
        <div className="modal-overlay" onClick={() => setShowEncounterPicker(false)}>
          <div className="modal-content" onClick={e => e.stopPropagation()}>
            <div className="modal-header">
              <h3 className="font-semibold">Select Active Encounter</h3>
              <button onClick={() => setShowEncounterPicker(false)} className="text-[var(--text-secondary)] hover:text-[var(--text-primary)]">
                <X size={18} />
              </button>
            </div>
            <div className="modal-body space-y-2 max-h-80 overflow-y-auto">
              {encounters.length === 0 ? (
                <p className="text-sm text-[var(--text-secondary)] text-center py-8">No active encounters found. Create an encounter first.</p>
              ) : encounters.map((enc: any) => (
                <button key={enc.id}
                  onClick={() => { setSelectedEncounter(enc); setShowEncounterPicker(false); }}
                  className={`w-full text-left p-4 rounded-xl border transition-all hover:shadow-sm ${
                    selectedEncounter?.id === enc.id ? "border-[var(--accent-primary)] bg-[var(--accent-primary-light)]" : "border-[var(--border)] hover:border-slate-300"}`}>
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm font-medium">{enc.encounter_type || "Visit"} — {enc.department || "General"}</p>
                      <p className="text-xs text-[var(--text-secondary)] mt-0.5">
                        Patient: {enc.patient_id?.slice(0, 8)}... · {new Date(enc.created_at).toLocaleDateString()}
                      </p>
                    </div>
                    <span className={`badge-${enc.status === "active" ? "success" : "neutral"}`}>{enc.status}</span>
                  </div>
                </button>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Create order modal */}
      {selectedEncounter && (
        <CreateOrderModal
          open={showCreate}
          onClose={() => setShowCreate(false)}
          encounterId={selectedEncounter.id}
          patientId={selectedEncounter.patient_id}
          onCreated={() => loadOrders(selectedEncounter.id)}
        />
      )}

      {/* Create Template Modal */}
      {showCreateTemplate && (
        <div className="modal-overlay" onClick={() => setShowCreateTemplate(false)}>
          <div className="bg-white rounded-2xl shadow-2xl w-full max-w-xl mx-4 max-h-[90vh] overflow-hidden flex flex-col"
            onClick={e => e.stopPropagation()} style={{ animation: "slideUp 0.3s ease-out" }}>
            <div className="px-6 py-4 border-b border-[var(--border)] flex items-center justify-between bg-gradient-to-r from-purple-600 to-blue-600">
              <div className="flex items-center gap-3">
                <div className="w-9 h-9 bg-white/20 rounded-lg flex items-center justify-center backdrop-blur-sm">
                  <Layers size={18} className="text-white" />
                </div>
                <h3 className="text-base font-semibold text-white">New Template</h3>
              </div>
              <button onClick={() => setShowCreateTemplate(false)} className="text-white/70 hover:text-white"><X size={18} /></button>
            </div>
            <div className="flex-1 overflow-y-auto p-6 space-y-4">
              <div>
                <label className="input-label">Template Name *</label>
                <input value={tplForm.name} onChange={e => setTplForm({...tplForm, name: e.target.value})}
                  placeholder="e.g., Pneumonia Workup" className="input-field" />
              </div>
              <div>
                <label className="input-label">Description</label>
                <input value={tplForm.desc} onChange={e => setTplForm({...tplForm, desc: e.target.value})}
                  placeholder="Brief description of this template" className="input-field" />
              </div>
              <div>
                <label className="input-label">Order Type *</label>
                <div className="flex flex-wrap gap-2">
                  {ORDER_TYPES.map(t => {
                    const Icon = t.icon; const sel = tplForm.type === t.value;
                    return (
                      <button key={t.value} onClick={() => setTplForm({...tplForm, type: t.value})}
                        className={`flex items-center gap-2 px-3 py-2 rounded-lg border text-xs font-medium transition-all ${
                          sel ? "border-2 shadow-sm" : "border-[var(--border)] hover:border-slate-300"}`}
                        style={sel ? { borderColor: t.color, background: t.bg, color: t.color } : {}}>
                        <Icon size={14} /> {t.label}
                      </button>
                    );
                  })}
                </div>
              </div>
              {/* Add items via catalog search */}
              <div>
                <label className="input-label">Items — Search to add</label>
                <div className="relative">
                  <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-[var(--text-secondary)]" />
                  <input value={tplSearch} onChange={e => { setTplSearch(e.target.value); searchCatalogFor(e.target.value, setTplCatalog); }}
                    placeholder="Search catalog..." className="input-field pl-9" />
                </div>
                {tplCatalog.length > 0 && (
                  <div className="border border-[var(--border)] rounded-lg mt-1 max-h-32 overflow-y-auto divide-y divide-[var(--border)]">
                    {tplCatalog.map((c: any, i: number) => (
                      <button key={i} onClick={() => {
                        if (!tplForm.items.find((x: any) => x.item_name === c.name))
                          setTplForm({...tplForm, items: [...tplForm.items, { item_type: "item", item_name: c.name, item_code: c.code }]});
                        setTplSearch(""); setTplCatalog([]);
                      }} className="w-full flex items-center gap-2 px-3 py-2 text-left hover:bg-slate-50 text-xs">
                        <Plus size={12} className="text-[var(--text-secondary)]" />{c.name} <span className="text-[var(--text-secondary)] ml-auto">{c.code}</span>
                      </button>
                    ))}
                  </div>
                )}
                {tplForm.items.length > 0 && (
                  <div className="mt-2 space-y-1">
                    {tplForm.items.map((item: any, i: number) => (
                      <div key={i} className="flex items-center gap-2 px-3 py-2 rounded-lg bg-slate-50 border border-slate-100">
                        <CheckCircle2 size={14} className="text-green-500" />
                        <span className="text-xs font-medium flex-1">{item.item_name}</span>
                        <button onClick={() => setTplForm({...tplForm, items: tplForm.items.filter((_: any, j: number) => j !== i)})}
                          className="text-red-400 hover:text-red-600"><X size={12} /></button>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
            <div className="px-6 py-4 border-t border-[var(--border)] flex justify-end gap-2 bg-slate-50">
              <button onClick={() => setShowCreateTemplate(false)} className="btn-secondary btn-sm">Cancel</button>
              <button onClick={submitTemplate} disabled={!tplForm.name || !tplForm.type || tplForm.items.length === 0}
                className="btn-primary btn-sm"><Check size={14} /> Create Template</button>
            </div>
          </div>
        </div>
      )}

      {/* Create Order Set Modal */}
      {showCreateSet && (
        <div className="modal-overlay" onClick={() => setShowCreateSet(false)}>
          <div className="bg-white rounded-2xl shadow-2xl w-full max-w-xl mx-4 max-h-[90vh] overflow-hidden flex flex-col"
            onClick={e => e.stopPropagation()} style={{ animation: "slideUp 0.3s ease-out" }}>
            <div className="px-6 py-4 border-b border-[var(--border)] flex items-center justify-between bg-gradient-to-r from-sky-600 to-emerald-600">
              <div className="flex items-center gap-3">
                <div className="w-9 h-9 bg-white/20 rounded-lg flex items-center justify-center backdrop-blur-sm">
                  <Package size={18} className="text-white" />
                </div>
                <h3 className="text-base font-semibold text-white">New Order Set</h3>
              </div>
              <button onClick={() => setShowCreateSet(false)} className="text-white/70 hover:text-white"><X size={18} /></button>
            </div>
            <div className="flex-1 overflow-y-auto p-6 space-y-4">
              <div>
                <label className="input-label">Set Name *</label>
                <input value={setForm.name} onChange={e => setSetForm({...setForm, name: e.target.value})}
                  placeholder="e.g., ER Chest Pain Protocol" className="input-field" />
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="input-label">Description</label>
                  <input value={setForm.desc} onChange={e => setSetForm({...setForm, desc: e.target.value})}
                    placeholder="Brief description" className="input-field" />
                </div>
                <div>
                  <label className="input-label">Clinical Context</label>
                  <select value={setForm.context} onChange={e => setSetForm({...setForm, context: e.target.value})} className="input-field">
                    <option value="">Select...</option>
                    <option value="Emergency">Emergency</option>
                    <option value="ICU">ICU</option>
                    <option value="Surgery">Surgery</option>
                    <option value="General">General</option>
                    <option value="Pediatrics">Pediatrics</option>
                    <option value="OPD">OPD</option>
                  </select>
                </div>
              </div>
              {/* Add items — with type selection for each */}
              <div>
                <label className="input-label">Items — Search to add (multi-domain)</label>
                <div className="relative">
                  <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-[var(--text-secondary)]" />
                  <input value={setSearch} onChange={e => { setSetSearch(e.target.value); searchCatalogFor(e.target.value, setSetCatalog); }}
                    placeholder="Search labs, meds, imaging..." className="input-field pl-9" />
                </div>
                {setCatalog.length > 0 && (
                  <div className="border border-[var(--border)] rounded-lg mt-1 max-h-32 overflow-y-auto divide-y divide-[var(--border)]">
                    {setCatalog.map((c: any, i: number) => {
                      const t = ORDER_TYPES.find(o => o.value === c.type);
                      const Icon = t?.icon || Zap;
                      return (
                        <button key={i} onClick={() => {
                          if (!setForm.items.find((x: any) => x.item_name === c.name))
                            setSetForm({...setForm, items: [...setForm.items, { order_type: c.type, item_name: c.name, item_code: c.code, sort_order: setForm.items.length }]});
                          setSetSearch(""); setSetCatalog([]);
                        }} className="w-full flex items-center gap-2 px-3 py-2 text-left hover:bg-slate-50 text-xs">
                          <Icon size={12} style={{ color: t?.color }} />
                          {c.name}
                          <span className="text-[var(--text-secondary)] ml-auto px-1.5 py-0.5 rounded bg-slate-50 text-[10px]">{t?.label}</span>
                        </button>
                      );
                    })}
                  </div>
                )}
                {setForm.items.length > 0 && (
                  <div className="mt-2 space-y-1">
                    {setForm.items.map((item: any, i: number) => {
                      const t = ORDER_TYPES.find(o => o.value === item.order_type);
                      const Icon = t?.icon || Zap;
                      return (
                        <div key={i} className="flex items-center gap-2 px-3 py-2 rounded-lg bg-slate-50 border border-slate-100">
                          <Icon size={14} style={{ color: t?.color }} />
                          <span className="text-xs font-medium flex-1">{item.item_name}</span>
                          <span className="text-[10px] px-1.5 py-0.5 rounded bg-white border border-slate-100" style={{ color: t?.color }}>{t?.label}</span>
                          <button onClick={() => setSetForm({...setForm, items: setForm.items.filter((_: any, j: number) => j !== i)})}
                            className="text-red-400 hover:text-red-600"><X size={12} /></button>
                        </div>
                      );
                    })}
                  </div>
                )}
              </div>
            </div>
            <div className="px-6 py-4 border-t border-[var(--border)] flex justify-end gap-2 bg-slate-50">
              <button onClick={() => setShowCreateSet(false)} className="btn-secondary btn-sm">Cancel</button>
              <button onClick={submitOrderSet} disabled={!setForm.name || setForm.items.length === 0}
                className="btn-primary btn-sm"><Check size={14} /> Create Order Set</button>
            </div>
          </div>
        </div>
      )}

      <style jsx>{`
        @keyframes slideUp {
          from { opacity: 0; transform: translateY(20px); }
          to { opacity: 1; transform: translateY(0); }
        }
        .animate-in {
          animation: slideUp 0.2s ease-out;
        }
      `}</style>
    </div>
  );
}

