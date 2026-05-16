type SegmentedOption<T extends string> = {
  value: T;
  label: string;
  title?: string;
};

type SegmentedProps<T extends string> = {
  value: T;
  options: SegmentedOption<T>[];
  onChange: (value: T) => void;
  disabled?: boolean;
  "aria-label": string;
};

export function Segmented<T extends string>({
  value,
  options,
  onChange,
  disabled,
  "aria-label": ariaLabel,
}: SegmentedProps<T>) {
  return (
    <div
      className="segmented"
      role="radiogroup"
      aria-label={ariaLabel}
      aria-disabled={disabled || undefined}
    >
      {options.map((opt) => {
        const selected = opt.value === value;
        return (
          <button
            key={opt.value}
            type="button"
            role="radio"
            aria-checked={selected}
            title={opt.title}
            disabled={disabled}
            className={`segmented__btn${selected ? " segmented__btn--active" : ""}`}
            onClick={() => onChange(opt.value)}
          >
            {opt.label}
          </button>
        );
      })}
    </div>
  );
}
