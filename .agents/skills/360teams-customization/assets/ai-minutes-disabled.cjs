const disabled = () => ({ bizCode: 40301, msg: 'AI 灵记已停用', disabled: true });
module.exports = {
  getStatus() {
    return { disabled: true, state: 'idle', taskId: '', meetingJoinUrl: '', startTime: 0,
      recordingDurationMs: 0, pauseReason: '', audioConfig: { microphones: [], selectedMicrophoneId: '',
        systemAudio: { supported: false, platform: process.platform, permission: 'not-determined', enabled: false } } };
  },
  async record() { return disabled(); },
  async audioConfig() { return disabled(); },
  publishAudioEvent() { return disabled(); },
};
