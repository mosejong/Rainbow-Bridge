function Button({ children, onClick, variant = 'primary', disabled = false, type = 'button', className = '' }) {
  const base = 'px-5 py-2.5 rounded-xl font-semibold transition-colors disabled:opacity-50 disabled:cursor-not-allowed';

  const variants = {
    primary: 'bg-violet-500 hover:bg-violet-600 text-white',
    danger: 'bg-red-500 hover:bg-red-600 text-white',
    ghost: 'border border-violet-400 text-violet-600 hover:bg-violet-50',
  };

  return (
    <button
      type={type}
      onClick={onClick}
      disabled={disabled}
      className={`${base} ${variants[variant]} ${className}`}
    >
      {children}
    </button>
  );
}

export default Button;
