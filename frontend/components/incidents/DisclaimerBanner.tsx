import { AlertTriangle } from 'lucide-react';

interface DisclaimerBannerProps {
  text?: string;
}

const DEFAULT_DISCLAIMER =
  'This AI-generated report is a tool to assist human security operators. ' +
  'It does not constitute evidence, does not identify individuals, and must not ' +
  'be used as the sole basis for any enforcement, legal, or security action. ' +
  'All findings require human verification and judgment.';

export default function DisclaimerBanner({ text }: DisclaimerBannerProps) {
  return (
    <div className="flex gap-3 rounded-lg border border-yellow-500/30 bg-yellow-500/8 p-4">
      <AlertTriangle className="w-5 h-5 text-yellow-400 shrink-0 mt-0.5" />
      <div>
        <p className="text-xs font-semibold text-yellow-400 uppercase tracking-wider mb-1">
          Human Review Required
        </p>
        <p className="text-sm text-yellow-300/80 leading-relaxed">
          {text ?? DEFAULT_DISCLAIMER}
        </p>
      </div>
    </div>
  );
}
