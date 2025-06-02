(function() {
  // Create widget container
  const container = document.createElement('div');
  container.id = 'ai-chatbot-widget';
  container.style.position = 'fixed';
  container.style.bottom = '20px';
  container.style.right = '20px';
  container.style.zIndex = '9999';
  
  // Get the script tag
  const scriptTag = document.currentScript;
  
  // Get customization options
  const position = scriptTag.getAttribute('data-position') || 'right';
  const color = scriptTag.getAttribute('data-color') || '#4a69bd';
  const domain = scriptTag.getAttribute('data-domain');
  
  if (position === 'left') {
    container.style.left = '20px';
    container.style.right = 'auto';
  }
  
  // Create chat button
  const button = document.createElement('button');
  button.innerHTML = '💬';
  button.style.width = '50px';
  button.style.height = '50px';
  button.style.borderRadius = '50%';
  button.style.backgroundColor = color;
  button.style.color = 'white';
  button.style.border = 'none';
  button.style.fontSize = '24px';
  button.style.cursor = 'pointer';
  button.style.boxShadow = '0 2px 10px rgba(0,0,0,0.2)';
  
  // Create iframe for chat (hidden by default)
  const iframe = document.createElement('iframe');
  iframe.src = domain + '/embed';
  iframe.style.width = '350px';
  iframe.style.height = '500px';
  iframe.style.border = 'none';
  iframe.style.borderRadius = '10px';
  iframe.style.boxShadow = '0 5px 15px rgba(0,0,0,0.2)';
  iframe.style.display = 'none';
  iframe.style.marginBottom = '10px';
  
  // Add elements to container
  container.appendChild(iframe);
  container.appendChild(button);
  
  // Add container to body
  document.body.appendChild(container);
  
  // Toggle chat on button click
  button.addEventListener('click', function() {
    if (iframe.style.display === 'none') {
      iframe.style.display = 'block';
    } else {
      iframe.style.display = 'none';
    }
  });
})();