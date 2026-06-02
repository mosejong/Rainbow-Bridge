function SafetyModal({ isOpen, onClose }) {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div className="bg-white rounded-2xl p-6 mx-4 max-w-sm w-full text-center shadow-xl">
        <div className="text-5xl mb-3">⚠️</div>
        <h2 className="text-xl font-bold text-red-600 mb-2">힘드신가요?</h2>
        <p className="text-gray-600 mb-6 leading-relaxed">
          지금 많이 힘드시다면<br />
          전문가와 이야기해보세요.
        </p>
        <a
          href="tel:1393"
          className="block bg-red-500 hover:bg-red-600 text-white py-3 rounded-xl font-bold text-lg mb-3 transition-colors"
        >
          📞 정신건강 위기상담 1393
        </a>
        <button
          onClick={onClose}
          className="text-gray-400 text-sm hover:text-gray-600"
        >
          닫기
        </button>
      </div>
    </div>
  );
}

export default SafetyModal;
