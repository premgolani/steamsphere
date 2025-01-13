let isLoginMode = true;

function openAuthModal(type) {
    isLoginMode = type === 'login';
    const modal = document.getElementById('authModal');
    if (!modal) {
        console.error('Auth modal not found');
        return;
    }
    
    modal.style.display = 'flex';
    setTimeout(() => modal.classList.add('active'), 10);
    
    document.getElementById('authTitle').textContent = isLoginMode ? 'Login' : 'Register';
    document.getElementById('roleGroup').style.display = isLoginMode ? 'none' : 'block';
    document.querySelector('.auth-btn').textContent = isLoginMode ? 'Login' : 'Sign Up';
    
    const switchText = isLoginMode ? 
        'Not registered? <a href="#" onclick="toggleAuthMode(); return false;">Sign up</a>' : 
        'Already registered? <a href="#" onclick="toggleAuthMode(); return false;">Login</a>';
    document.querySelector('.switch-auth').innerHTML = switchText;
}

function closeAuthModal() {
    const modal = document.getElementById('authModal');
    if (!modal) return;
    
    modal.classList.remove('active');
    setTimeout(() => {
        modal.style.display = 'none';
        document.getElementById('authForm').reset();
    }, 300);
}

function toggleAuthMode() {
    isLoginMode = !isLoginMode;
    openAuthModal(isLoginMode ? 'login' : 'register');
}

async function handleAuth(e) {
    e.preventDefault();
    
    const username = document.getElementById('username').value.trim();
    const password = document.getElementById('password').value.trim();
    const role = document.getElementById('role')?.value || 'user';
    
    if(!username || !password) {
        showNotification('Please fill all fields', 'error');
        return;
    }
    
    try {
        const response = await fetch(`/${isLoginMode ? 'login' : 'register'}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ username, password, role })
        });

        const data = await response.json();
        
        if (!response.ok) {
            throw new Error(data.error || 'Authentication failed');
        }

        if (data.success) {
            showNotification(
                isLoginMode ? 'Login successful!' : 'Account created successfully!', 
                'success'
            );
            closeAuthModal();
            setTimeout(() => window.location.reload(), 1000);
        }
    } catch (error) {
        console.error('Auth error:', error);
        showNotification(error.message, 'error');
    }
}

function showNotification(message, type) {
    const notification = document.createElement('div');
    notification.className = `notification ${type}`;
    notification.textContent = message;
    
    document.body.appendChild(notification);
    
    setTimeout(() => {
        notification.classList.add('show');
        setTimeout(() => {
            notification.classList.remove('show');
            setTimeout(() => notification.remove(), 300);
        }, 3000);
    }, 100);
}
let currentVideoId = null;

function openCommentModal(videoId) {
  currentVideoId = videoId;
  const modal = document.getElementById('commentsModal');
  modal.style.display = 'block';
  loadComments(videoId);
}

function fetchComments(videoId) {
    fetch(`/api/comments/${videoId}`)
        .then(response => response.json())
        .then(comments => {
            const commentsList = document.getElementById('commentsList');
            commentsList.innerHTML = comments.map(comment => `
                <div class="comment">
                    <div class="comment-header">
                        <strong>${comment.username}</strong>
                        <span class="comment-date">${new Date(comment.created_at).toLocaleDateString()}</span>
                    </div>
                    <p>${comment.text}</p>
                </div>
            `).join('');
        });
}

document.getElementById('commentForm').addEventListener('submit', function(e) {
  e.preventDefault();
  const input = document.getElementById('commentInput');
  const comment = input.value.trim();
  
  if (!comment) return;

  fetch(`/comment/${currentVideoId}`, {
      method: 'POST',
      headers: {
          'Content-Type': 'application/json',
      },
      body: JSON.stringify({ comment: comment })
  })
  .then(response => response.json())
  .then(data => {
      if (data.success) {
          input.value = '';
          loadComments(currentVideoId); 
      }
  })
  .catch(error => console.error('Error posting comment:', error));
});


document.querySelector('.close').onclick = function() {
    document.getElementById('commentsModal').style.display = 'none';
}

function closeCommentModal() {
    const modal = document.getElementById('commentsModal');
    modal.style.display = 'none';
    currentVideoId = null;
}


async function handleLike(videoId) {
    try {
        const response = await fetch(`/like/${videoId}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' }
        });
        
        const data = await response.json();
        if (response.ok) {
            const likeBtn = document.querySelector(`[data-video-id="${videoId}"] .like-btn`);
            const count = likeBtn.querySelector('.count');
            likeBtn.classList.toggle('liked');
            count.textContent = data.likes;
        } else {
            throw new Error(data.error);
        }
    } catch (error) {
        console.error('Like error:', error);
    }
}

function loadComments(videoId) {
  fetch(`/comments/${videoId}`)
      .then(response => response.json())
      .then(data => {
          const commentsList = document.getElementById('commentsList');
          commentsList.innerHTML = ''; 
          
          if (Array.isArray(data)) {
              data.forEach(comment => {
                  const commentElement = document.createElement('div');
                  commentElement.className = 'comment';
                  commentElement.innerHTML = `
                      <div class="comment-header">
                          <strong>${comment.username}</strong>
                          <span class="timestamp">${new Date(comment.timestamp).toLocaleString()}</span>
                      </div>
                      <div class="comment-text">${comment.text}</div>
                  `;
                  commentsList.appendChild(commentElement);
              });
          } else {
              console.error('Invalid comment data received:', data);
          }
      })
      .catch(error => {
          console.error('Error loading comments:', error);
      });
}


document.addEventListener('DOMContentLoaded', function() {
    
    const closeBtn = document.querySelector('.modal .close');
    if (closeBtn) {
        closeBtn.onclick = closeCommentModal;
    }

    
    const commentForm = document.getElementById('commentForm');
    if (commentForm) {
        commentForm.onsubmit = async function(e) {
            e.preventDefault();
            const input = document.getElementById('commentInput');
            const comment = input.value.trim();
            
            if (!comment || !currentVideoId) return;

            try {
                const response = await fetch(`/comment/${currentVideoId}`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ comment })
                });
                
                if (response.ok) {
                    input.value = '';
                    await loadComments(currentVideoId);
                    const commentBtn = document.querySelector(`[data-video-id="${currentVideoId}"] .comment-btn .count`);
                    const currentCount = parseInt(commentBtn.textContent);
                    commentBtn.textContent = currentCount + 1;
                }
            } catch (error) {
                console.error('Post comment error:', error);
            }
        };
    }

    
    window.onclick = function(event) {
        const modal = document.getElementById('commentsModal');
        if (event.target == modal) {
            closeCommentModal();
        }
    };
});


document.addEventListener('DOMContentLoaded', () => {
  const videoCards = document.querySelectorAll('.video-card');
  
  videoCards.forEach(card => {
      const video = card.querySelector('video');
      
      card.addEventListener('mouseenter', () => {
          video.play();
          document.body.style.overflow = 'hidden';
      });
      
      card.addEventListener('mouseleave', () => {
          video.pause();
          video.currentTime = 0;
          document.body.style.overflow = 'auto';
      });
  });
});


document.getElementById('profilePicInput').addEventListener('change', async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    
    const profileImage = document.getElementById('profileImage');
    profileImage.style.opacity = '0.5';

    const formData = new FormData();
    formData.append('profile_pic', file);

    try {
        const response = await fetch('/update_profile_pic', {
            method: 'POST',
            body: formData
        });

        const data = await response.json();
        
        if (data.success) {
            
            profileImage.src = data.image_url;
            showNotification('Profile picture updated successfully', 'success');
        } else {
            throw new Error(data.error || 'Failed to update profile picture');
        }
    } catch (error) {
        console.error('Update profile picture error:', error);
        showNotification(error.message, 'error');
    } finally {
        
        profileImage.style.opacity = '1';
    }
});


