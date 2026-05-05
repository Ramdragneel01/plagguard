interface Props {
    value: number; // 0 – 1
    label: string;
    color?: string;
}

export function ProgressBar({ value, label, color }: Props) {
    const pct = Math.round(value * 100);
    const barColor =
        color ||
        (pct >= 60
            ? 'bg-red-500'
            : pct >= 40
                ? 'bg-orange-500'
                : pct >= 20
                    ? 'bg-yellow-500'
                    : 'bg-green-500');

    return (
        <div>
            <div className="flex justify-between mb-1 text-sm">
                <span className="text-slate-400">{label}</span>
                <span className="font-semibold">{pct}%</span>
            </div>
            <div className="w-full h-2.5 bg-slate-800 rounded-full overflow-hidden">
                <div
                    className={`h-full rounded-full transition-all duration-700 ease-out ${barColor}`}
                    style={{ width: `${pct}%` }}
                />
            </div>
        </div>
    );
}
