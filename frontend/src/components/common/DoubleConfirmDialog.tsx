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
      <div className="flex gap-3 rounded-xl border border-amber-200 bg-amber-50 p-4 text-sm text-amber-950">
        <AlertTriangle className="mt-0.5 h-5 w-5 shrink-0 text-amber-700" />
        <p>{step === 1 ? description : `Please confirm one more time: ${actionLabel.toLowerCase()}?`}</p>
      </div>
      {step === 1 ? <div className="flex justify-end gap-2"><button type="button" onClick={close} className="rounded-lg border border-slate-300 px-4 py-2 text-sm font-semibold text-slate-700">Cancel</button><button type="button" disabled={busy} onClick={() => setStep(2)} className="rounded-lg bg-amber-600 px-4 py-2 text-sm font-bold text-white hover:bg-amber-700 disabled:opacity-50">Continue</button></div>
        : <div className="flex justify-end gap-2"><button type="button" disabled={busy} onClick={() => setStep(1)} className="rounded-lg border border-slate-300 px-4 py-2 text-sm font-semibold text-slate-700 disabled:opacity-50">Go back</button><button type="button" disabled={busy} onClick={() => void Promise.resolve(onConfirm()).catch(() => {})} className="rounded-lg bg-rose-700 px-4 py-2 text-sm font-bold text-white hover:bg-rose-800 disabled:opacity-50">{busy ? 'Working…' : `Confirm ${actionLabel}`}</button></div>}
    </div>
  </Modal>;
};
