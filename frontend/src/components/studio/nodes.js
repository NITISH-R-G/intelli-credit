import React, { memo } from 'react';
import { Handle, Position } from 'reactflow';
import {
  AlertTriangle,
  Building2,
  CheckCircle2,
  FileText,
  Play,
  RefreshCw,
  Share2,
} from 'lucide-react';

const runtimeTone = {
  idle: {
    badge: 'bg-slate-100 text-slate-500',
    ring: 'border-slate-200',
  },
  running: {
    badge: 'bg-blue-50 text-blue-600 border border-blue-100',
    ring: 'border-blue-400 shadow-blue-500/10',
  },
  retrying: {
    badge: 'bg-amber-50 text-amber-600 border border-amber-100',
    ring: 'border-amber-400 shadow-amber-500/10',
  },
  success: {
    badge: 'bg-emerald-50 text-emerald-600 border border-emerald-100',
    ring: 'border-emerald-400 shadow-emerald-500/10',
  },
  failed: {
    badge: 'bg-rose-50 text-rose-600 border border-rose-100',
    ring: 'border-rose-400 shadow-rose-500/10',
  },
  skipped: {
    badge: 'bg-slate-100 text-slate-400',
    ring: 'border-slate-200',
  },
};

const getRuntime = (data) => data.runtime || { status: 'idle' };

const CustomHandle = ({ type, position, colorClass, id, style }) => (
  <Handle
    type={type}
    position={position}
    id={id}
    style={style}
    className={`w-3.5 h-3.5 ${colorClass} border-[2.5px] border-white transition-all hover:scale-125 z-50 rounded-full shadow-sm`}
  />
);

const RuntimeBadge = ({ data, inHeader = false }) => {
  const runtime = getRuntime(data);
  if (runtime.status === 'idle') return null;
  const tone = runtimeTone[runtime.status] || runtimeTone.idle;

  return (
    <div className={`px-2 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wide ${tone.badge} ${!inHeader ? 'absolute top-3 right-3' : ''}`}>
      {runtime.status}
    </div>
  );
};

const ErrorHandle = () => (
  <CustomHandle
    type="source"
    position={Position.Right}
    id="error"
    colorClass="bg-rose-400"
    style={{ top: '50%' }}
  />
);

// Unified Node Container wrapper
const NodeCard = ({ children, selected, data, minWidth = 'min-w-[260px]' }) => {
  const runtime = getRuntime(data);
  const tone = runtimeTone[runtime.status] || runtimeTone.idle;
  
  return (
    <div className={`relative ${minWidth} bg-white rounded-2xl shadow-sm border ${selected ? 'border-blue-500 shadow-md ring-1 ring-blue-500/20' : runtime.status !== 'idle' ? tone.ring : 'border-slate-200 hover:border-slate-300'} transition-all text-left flex flex-col`}>
      {children}
    </div>
  );
};

// Unified Header
const NodeHeader = ({ icon: Icon, title, subtitle, iconTone, data }) => (
  <div className="flex items-center gap-3 p-3 border-b border-slate-100 bg-slate-50/50 rounded-t-2xl">
    <div className={`w-8 h-8 rounded-xl flex items-center justify-center shrink-0 ${iconTone}`}>
      <Icon className="w-4 h-4" />
    </div>
    <div className="flex flex-col min-w-0 pr-2 flex-1">
      <span className="text-[10px] font-bold uppercase tracking-[0.15em] text-slate-400 truncate">{subtitle}</span>
      <span className="text-sm font-semibold text-slate-800 truncate">{title}</span>
    </div>
    <RuntimeBadge data={data} inHeader={true} />
  </div>
);

export const TriggerNode = memo(({ data, selected }) => {
  return (
    <NodeCard selected={selected} data={data} minWidth="min-w-[220px]">
      <div className="p-4 flex items-center gap-4">
        <div className="w-12 h-12 rounded-full bg-emerald-50 border border-emerald-100 flex items-center justify-center text-emerald-600 shrink-0">
          <Play className="w-5 h-5 ml-0.5" />
        </div>
        <div className="flex flex-col">
          <span className="text-[10px] font-bold uppercase tracking-widest text-slate-400">Initiation</span>
          <span className="text-sm font-semibold text-slate-800">{data.label || 'Manual Trigger'}</span>
        </div>
      </div>
      <CustomHandle type="source" position={Position.Bottom} colorClass="bg-slate-400" />
    </NodeCard>
  );
});

export const DocumentClassificationNode = memo(({ data, selected }) => {
  const runtime = getRuntime(data);
  
  return (
    <NodeCard selected={selected} data={data} minWidth="w-[300px]">
      <NodeHeader 
        icon={FileText} 
        title={data.label || 'Document Classifier'} 
        subtitle="IDP Extraction"
        iconTone="bg-violet-100 text-violet-600"
        data={data}
      />

      <div className="flex flex-col">
        {data.confidence && (
          <div className="px-4 py-2 border-b border-slate-100 flex items-center justify-between bg-white">
            <span className="text-[10px] font-semibold text-slate-500 uppercase">Confidence</span>
            <div className="flex items-center gap-1.5 bg-emerald-50 text-emerald-700 px-2 py-0.5 rounded-md border border-emerald-100">
              <CheckCircle2 className="w-3 h-3" />
              <span className="text-xs font-bold">{data.confidence}%</span>
            </div>
          </div>
        )}

        {data.error && (
          <div className="p-3 bg-rose-50 border-b border-rose-100 flex items-start gap-2">
            <AlertTriangle className="w-4 h-4 text-rose-600 shrink-0 mt-0.5" />
            <div className="flex-1">
              <p className="text-xs text-rose-700 font-medium leading-relaxed">{data.error}</p>
              <button className="mt-2 text-[10px] font-semibold bg-white border border-rose-200 text-rose-700 px-3 py-1.5 rounded-lg flex items-center gap-1.5 hover:bg-rose-50 transition-colors shadow-sm">
                <RefreshCw className="w-3 h-3" /> Retry Extraction
              </button>
            </div>
          </div>
        )}

        {!data.error && data.extractedFields && (
          <div className="p-3 bg-white border-b border-slate-100">
            <span className="text-[10px] uppercase font-bold tracking-wider text-slate-400 mb-2 block px-1">Extracted Entities</span>
            <div className="bg-slate-50/50 rounded-xl border border-slate-100 overflow-hidden">
              {data.extractedFields.map((field, idx) => (
                <div key={idx} className={`flex justify-between items-center p-2 px-3 text-[11px] ${idx !== data.extractedFields.length - 1 ? 'border-b border-slate-100' : ''}`}>
                  <span className="text-slate-500 font-medium">{field.key}</span>
                  <span className="text-slate-800 font-semibold font-mono">{field.value}</span>
                </div>
              ))}
            </div>
          </div>
        )}

        <div className="px-4 py-2.5 bg-slate-50 flex justify-between items-center rounded-b-2xl">
          <span className="text-[10px] text-slate-400 font-medium">Model: <span className="text-slate-600 font-semibold">{data.model || 'SciBERT+Flan-T5'}</span></span>
          {runtime.durationMs != null && <span className="text-[10px] text-slate-400 font-mono">{runtime.durationMs}ms</span>}
        </div>
      </div>

      <CustomHandle type="target" position={Position.Top} colorClass="bg-slate-300" />
      <CustomHandle type="source" position={Position.Bottom} colorClass="bg-blue-500" />
      <ErrorHandle />
    </NodeCard>
  );
});

export const IntegrationNode = memo(({ data, selected }) => {
  const runtime = getRuntime(data);
  
  return (
    <NodeCard selected={selected} data={data}>
      <NodeHeader 
        icon={Building2} 
        title={data.label || 'Integration Call'} 
        subtitle={data.connection || 'API Gateway'}
        iconTone="bg-blue-100 text-blue-600"
        data={data}
      />

      <div className="p-3 flex flex-col gap-2 bg-white rounded-b-2xl">
        {data.warning && (
          <div className="bg-amber-50 border border-amber-100 rounded-xl p-2.5 flex items-start gap-2">
            <AlertTriangle className="w-4 h-4 text-amber-600 shrink-0 mt-0.5" />
            <span className="text-[11px] text-amber-800 font-medium leading-relaxed">{data.warningDetails || 'High latency detected down-stream.'}</span>
          </div>
        )}

        {runtime.error && (
          <div className="bg-rose-50 border border-rose-100 rounded-xl p-2.5 text-[11px] text-rose-700 font-medium leading-relaxed">
            {runtime.error}
          </div>
        )}
        
        {!data.warning && !runtime.error && (
          <div className="text-[11px] text-slate-500 font-medium px-1 py-1">
            Ready to execute external request.
          </div>
        )}
      </div>

      <CustomHandle type="target" position={Position.Top} colorClass="bg-slate-300" />
      <CustomHandle type="source" position={Position.Bottom} colorClass="bg-blue-500" />
      <ErrorHandle />
    </NodeCard>
  );
});

export const ConditionNode = memo(({ data, selected }) => {
  const runtime = getRuntime(data);
  
  return (
    <NodeCard selected={selected} data={data} minWidth="w-[280px]">
      <NodeHeader 
        icon={Share2} 
        title={data.label || 'Condition Check'} 
        subtitle="Routing Logic"
        iconTone="bg-rose-100 text-rose-600"
        data={data}
      />

      <div className="p-4 bg-white rounded-b-2xl flex flex-col gap-3">
        <div className="bg-slate-50 rounded-xl p-3 border border-slate-100">
          <span className="text-[11px] text-slate-600 font-mono break-all line-clamp-3 leading-relaxed">
            {data.expression || data.assignmentDetails || '{{ expressions.evaluate }}'}
          </span>
        </div>

        {runtime.output?.branch && (
          <div className="text-[10px] font-bold text-slate-400 uppercase tracking-widest text-center">
            Branch: <span className={runtime.output.branch === 'true' ? 'text-emerald-500' : 'text-rose-500'}>{runtime.output.branch}</span>
          </div>
        )}
      </div>

      <CustomHandle type="target" position={Position.Top} colorClass="bg-slate-300" />
      <CustomHandle type="source" position={Position.Bottom} id="true" colorClass="bg-emerald-500" style={{ left: '33%' }} />
      <CustomHandle type="source" position={Position.Bottom} id="false" colorClass="bg-rose-500" style={{ left: '67%' }} />

      <div className="absolute -bottom-[22px] w-full flex justify-between px-8 text-[9px] font-bold uppercase tracking-wider">
        <span className="text-emerald-600 bg-emerald-50/80 px-1.5 py-0.5 rounded shadow-sm border border-emerald-100/50 backdrop-blur-sm">True</span>
        <span className="text-rose-600 bg-rose-50/80 px-1.5 py-0.5 rounded shadow-sm border border-rose-100/50 backdrop-blur-sm">False</span>
      </div>
    </NodeCard>
  );
});

export const ExplainableAINode = memo(({ data, selected }) => {
  const runtime = getRuntime(data);
  
  return (
    <NodeCard selected={selected} data={data} minWidth="w-[300px]">
      <NodeHeader 
        icon={Share2} 
        title={data.label || 'TreeSHAP Explainer'} 
        subtitle="Interpretability"
        iconTone="bg-amber-100 text-amber-600"
        data={data}
      />

      <div className="flex flex-col bg-white">
        <div className="p-4 pt-3">
          <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400 mb-3 block">Feature Impact Drivers</span>
          
          {data.shapValues && (
            <div className="flex flex-col gap-3">
              {data.shapValues.map((feature, idx) => {
                const isPositive = feature.impact > 0;
                const absImpact = Math.min(Math.abs(feature.impact) * 20, 100);
                return (
                  <div key={idx} className="flex flex-col gap-1.5">
                    <div className="flex justify-between text-[10px] font-semibold items-center">
                      <span className="text-slate-600 truncate max-w-[180px]">{feature.name}</span>
                      <span className={isPositive ? 'text-emerald-600 bg-emerald-50 px-1.5 py-0.5 rounded' : 'text-rose-600 bg-rose-50 px-1.5 py-0.5 rounded'}>
                        {isPositive ? '+' : ''}{feature.impact.toFixed(2)}
                      </span>
                    </div>
                    <div className="w-full h-1.5 bg-slate-100 rounded-full overflow-hidden flex relative">
                      {/* Center line marker */}
                      <div className="absolute left-1/2 top-0 bottom-0 w-[1px] bg-slate-300 z-10" />
                      <div
                        className={`h-full absolute top-0 ${isPositive ? 'bg-emerald-400 rounded-r-full' : 'bg-rose-400 rounded-l-full'}`}
                        style={{
                          width: `${absImpact / 2}%`,
                          left: isPositive ? '50%' : `${50 - (absImpact / 2)}%`,
                        }}
                      />
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>

        <div className="px-4 py-2.5 border-t border-slate-100 bg-slate-50 flex justify-between items-center rounded-b-2xl">
          <span className="text-[10px] text-slate-400 font-medium">Model: <span className="text-slate-600 font-semibold">{data.modelReference || 'XGBoost v2'}</span></span>
          {runtime.output?.summary && <span className="text-[10px] text-slate-400 truncate max-w-[120px]">{runtime.output.summary}</span>}
        </div>
      </div>

      <CustomHandle type="target" position={Position.Top} colorClass="bg-slate-300" />
      <CustomHandle type="source" position={Position.Bottom} colorClass="bg-blue-500" />
      <ErrorHandle />
    </NodeCard>
  );
});

export const MCAFilingSyncNode = memo(({ data, selected }) => {
  return (
    <NodeCard selected={selected} data={data}>
      <NodeHeader 
        icon={Building2} 
        title={data.label || 'MCA V3 Gateway'} 
        subtitle="Regulator Sync"
        iconTone="bg-sky-100 text-sky-600"
        data={data}
      />
      <div className="p-3 bg-white rounded-b-2xl">
        {data.cinTarget && (
          <div className="bg-slate-50 border border-slate-100 rounded-xl p-2.5 text-[11px] font-mono text-slate-500 truncate flex items-center justify-between">
            <span>Target CIN</span>
            <span className="text-slate-800 font-semibold">{data.cinTarget}</span>
          </div>
        )}
      </div>
      <CustomHandle type="target" position={Position.Top} colorClass="bg-slate-300" />
      <CustomHandle type="source" position={Position.Bottom} colorClass="bg-blue-500" />
      <ErrorHandle />
    </NodeCard>
  );
});

export const EPFOAnomalyNode = memo(({ data, selected }) => {
  return (
    <NodeCard selected={selected} data={data}>
      <NodeHeader 
        icon={AlertTriangle} 
        title={data.label || 'EPFO Anomalies'} 
        subtitle="Compliance Check"
        iconTone="bg-orange-100 text-orange-600"
        data={data}
      />
      <div className="p-3 bg-white rounded-b-2xl">
        {data.employerIdTarget && (
          <div className="bg-slate-50 border border-slate-100 rounded-xl p-2.5 text-[11px] font-mono text-slate-500 truncate flex items-center justify-between">
            <span>EPFO ID</span>
            <span className="text-slate-800 font-semibold">{data.employerIdTarget}</span>
          </div>
        )}
      </div>
      <CustomHandle type="target" position={Position.Top} colorClass="bg-slate-300" />
      <CustomHandle type="source" position={Position.Bottom} colorClass="bg-blue-500" />
      <ErrorHandle />
    </NodeCard>
  );
});

TriggerNode.displayName = 'TriggerNode';
DocumentClassificationNode.displayName = 'DocumentClassificationNode';
IntegrationNode.displayName = 'IntegrationNode';
ConditionNode.displayName = 'ConditionNode';
ExplainableAINode.displayName = 'ExplainableAINode';
MCAFilingSyncNode.displayName = 'MCAFilingSyncNode';
EPFOAnomalyNode.displayName = 'EPFOAnomalyNode';


