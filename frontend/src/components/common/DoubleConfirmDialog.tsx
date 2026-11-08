import React, { useEffect, useState } from 'react';
import { AlertTriangle } from 'lucide-react';
import { Modal } from './Modal';

type DoubleConfirmDialogProps = {
  isOpen: boolean;
  title: string;
  description: string;
  actionLabel: string;
  busy?: boolean;
  onClose: () => void;
  onConfirm: () => void | Promise<void>;
};

export const DoubleConfirmDialog: React.FC<DoubleConfirmDialogProps> = ({
  isOpen, title, description, actionLabel, busy = false, onClose, onConfirm,
}) => {
  const [step, setStep] = useState(1);
  useEffect(() => { if (isOpen) setStep(1); }, [isOpen]);
  const close = () => { setStep(1); onClose(); };

  return <Modal isOpen={isOpen} onClose={close} title={title} subtitle={`Confirmation ${step} of 2`} maxWidth="md">
    <div className="space-y-5">
      <div className="flex gap-3 rounded-2xl border border-amber-200 dark:border-amber-900/40 bg-amber-50 dark:bg-amber-950/20 p-4 text-xs font-medium text-amber-950 dark:text-amber-200">
        <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0 text-amber-600 dark:text-amber-400" />
        <p className="leading-relaxed">{step === 1 ? description : `Please confirm one more time: ${actionLabel.toLowerCase()}?`}</p>
      </div>
      {step === 1 ? <div className="flex justify-end gap-2"><button type="button" onClick={close} className="rounded-xl border border-slate-300 dark:border-white/12 px-4 py-2 text-xs font-semibold text-slate-700 dark:text-zinc-300 hover:bg-slate-100 dark:hover:bg-white/10 cursor-pointer">Cancel</button><button type="button" disabled={busy} onClick={() => setStep(2)} className="rounded-xl bg-amber-600 px-4 py-2 text-xs font-bold text-white hover:bg-amber-500 shadow-sm disabled:opacity-50 cursor-pointer">Continue</button></div>
        : <div className="flex justify-end gap-2"><button type="button" disabled={busy} onClick={() => setStep(1)} className="rounded-xl border border-slate-300 dark:border-white/12 px-4 py-2 text-xs font-semibold text-slate-700 dark:text-zinc-300 disabled:opacity-50 hover:bg-slate-100 dark:hover:bg-white/10 cursor-pointer">Go back</button><button type="button" disabled={busy} onClick={() => void Promise.resolve(onConfirm()).catch(() => {})} className="rounded-xl bg-rose-600 px-4 py-2 text-xs font-bold text-white hover:bg-rose-500 shadow-sm disabled:opacity-50 cursor-pointer">{busy ? 'Working…' : `Confirm ${actionLabel}`}</button></div>}
    </div>
  </Modal>;
};
