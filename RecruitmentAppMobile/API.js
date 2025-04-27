import axios from 'axios';

const API_URL = 'http://192.168.1.80:8000/api/'; // Đảm bảo đây là địa chỉ IP chính xác của server Django của bạn

export const endpoints = {
    register: `${API_URL}register/`, // POST
    login: `${API_URL}token/`, // POST
    refreshToken: `${API_URL}token/refresh/`, // POST
    ntdRequest: `${API_URL}ntd-request/`, // POST
    approveNtdRequest: `${API_URL}approve-ntd-request/`, // POST
    ntdProfile: `${API_URL}ntd-profile/`, // GET, POST, PUT, PATCH
    ntvProfile: `${API_URL}ntv-profile/`, // GET, POST, PUT, PATCH
    changeActiveRole: `${API_URL}change-active-role/`, // POST
    jobPostings: `${API_URL}job-postings/`, // GET, POST
    jobPostingDetail: (id) => `${API_URL}job-postings/${id}/`, // GET, PUT, PATCH, DELETE
    approveJobPosting: (id) => `${API_URL}job-postings/${id}/approve/`, // POST
    rejectJobPosting: (id) => `${API_URL}job-postings/${id}/reject/`, // POST
    cvs: `${API_URL}cvs/`, // GET, POST
    cvDetail: (id) => `${API_URL}cvs/${id}/`, // GET, PUT, PATCH, DELETE
    applications: `${API_URL}applications/`, // GET, POST
    applicationDetail: (id) => `${API_URL}applications/${id}/`, // GET, PUT, PATCH, DELETE
    withdrawApplication: (id) => `${API_URL}applications/${id}/withdraw/`, // POST
    interviews: `${API_URL}interviews/`, // GET, POST
    interviewDetail: (id) => `${API_URL}interviews/${id}/`, // GET, PUT, PATCH, DELETE
    evaluateInterview: (id) => `${API_URL}interviews/${id}/evaluate/`, // POST
    notifications: `${API_URL}notifications/`, // GET, POST
    notificationDetail: (id) => `${API_URL}notifications/${id}/`, // GET, PUT, PATCH, DELETE
    markNotificationAsRead: (id) => `${API_URL}notifications/${id}/mark_as_read/`, // POST
    messages: `${API_URL}messages/`, // GET (with user_id param), POST
    userDetails: `${API_URL}users/`, // GET
    createConversation: `${API_URL}conversations/`, // POST
    conversationMessages: (id) => `${API_URL}conversations/${id}/messages/`, // GET
    sendConversationMessage: (id) => `${API_URL}conversations/${id}/messages/send/`, // POST
};

export const authAPI = (accessToken) => {
    return axios.create({
        baseURL: BASE_URL,
        headers: {
            Authorization: `Bearer ${accessToken}`,
            'Content-Type': 'application/json',
        },
    });
};

export default axios.create({
    baseURL: BASE_URL,

});