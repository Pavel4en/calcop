// Управление отображением пароля
document.addEventListener('DOMContentLoaded', function() {
  const passwordToggleButton = document.getElementById('password-toggle-button');
  
  if (passwordToggleButton) {
      passwordToggleButton.addEventListener('click', function() {
          const passwordField = document.getElementById('password-field');
          const passwordIcon = document.getElementById('password-icon');
          
          if (passwordField.type === 'password') {
              passwordField.type = 'text';
              passwordIcon.classList.remove('fa-eye');
              passwordIcon.classList.add('fa-eye-slash');
          } else {
              passwordField.type = 'password';
              passwordIcon.classList.remove('fa-eye-slash');
              passwordIcon.classList.add('fa-eye');
          }
      });
  }
  
  // Обработчик для кнопки закрытия уведомлений
  (document.querySelectorAll('.notification .delete') || []).forEach(($delete) => {
      const $notification = $delete.parentNode;
      $delete.addEventListener('click', () => {
          $notification.parentNode.removeChild($notification);
      });
  });
  
  // Автоматическое скрытие флеш-сообщений через 3 секунды
  setTimeout(() => {
      document.querySelectorAll('.flash-message').forEach(message => {
          message.style.opacity = '0';
          setTimeout(() => {
              if (message.parentNode) {
                  message.parentNode.removeChild(message);
              }
          }, 500);
      });
  }, 3000);
});