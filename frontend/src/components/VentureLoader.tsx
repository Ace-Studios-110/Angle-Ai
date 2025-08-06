type Props = {
  title: string
}
const VentureLoader = ({ title }: Props) => {
  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-tr from-slate-50 to-blue-50 px-4">
      <div className="flex flex-col items-center justify-center py-12">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-teal-600 mb-4" />
        <p className="text-gray-600 text-lg">{title}...</p>
      </div>
    </div>
  );
};

export default VentureLoader;
