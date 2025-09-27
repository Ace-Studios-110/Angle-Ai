interface AcceptModifyButtonsProps {
  onAccept: () => void;
  onModify: (currentText: string) => void;
  disabled?: boolean;
  currentText?: string;
}

export default function AcceptModifyButtons({ onAccept, onModify, disabled = false, currentText = "" }: AcceptModifyButtonsProps) {
  return (
    <div className="mt-4 flex justify-center gap-3">
      <button
        onClick={onAccept}
        disabled={disabled}
        className="px-6 py-2 bg-green-500 hover:bg-green-600 disabled:bg-gray-300 disabled:cursor-not-allowed text-white rounded-lg font-medium transition-colors duration-200 flex items-center gap-2"
      >
        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
        </svg>
        Accept
      </button>
      <button
        onClick={() => onModify(currentText)}
        disabled={disabled}
        className="px-6 py-2 bg-orange-500 hover:bg-orange-600 disabled:bg-gray-300 disabled:cursor-not-allowed text-white rounded-lg font-medium transition-colors duration-200 flex items-center gap-2"
      >
        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
        </svg>
        Modify
      </button>
    </div>
  );
}
