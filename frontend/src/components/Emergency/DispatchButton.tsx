/* High-priority emergency dispatch button. */

interface DispatchButtonProps {
  onDispatch: () => void | Promise<void>;
  disabled: boolean;
}

export function DispatchButton({ onDispatch, disabled }: DispatchButtonProps) {
  return (
    <button
      type="button"
      onClick={() => {
        void onDispatch();
      }}
      disabled={disabled}
      className="w-full rounded-3xl border border-um-red/40 bg-gradient-to-r from-um-red to-um-amber px-5 py-4 text-left font-display text-lg text-black transition hover:scale-[1.01] disabled:cursor-not-allowed disabled:opacity-50"
    >
      DISPATCH EMERGENCY VEHICLE
    </button>
  );
}
