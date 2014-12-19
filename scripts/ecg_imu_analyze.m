close all; clear all;

disp('------------------------------------------------------------------');
disp('------------------------------------------------------------------');

tRec = 60; % duration of recording
filename_end = 'min3_22bpm.csv';

imuData = csvread(strcat('../data/long_term_lying_down_10mins/cleaned_imu_', filename_end));
imu_fs = 100; % imu sampling frequency in Hz

ecgData = csvread(strcat('../data/long_term_lying_down_10mins/cleaned_ecg_', filename_end));
ecg_fs = 400; % ecg sampling frequency in Hz

ecgfft = fft(ecgData(:, 2));
br_filt_l = 0.1;
br_filt_h = 0.5;
br_filt_range = round(br_filt_l/ecg_fs*size(ecgfft,1)):round(br_filt_h/ecg_fs*size(ecgfft,1));
ecgfft(br_filt_range) = 0;
ecgfft(end+2-br_filt_range) = 0;
ecgbr = ifft(fft(ecgData(:, 2))-ecgfft);

plot((1:size(imuData, 1))/size(imuData, 1) * tRec, imuData(:, 3));
hold on;
plot((1:size(ecgData, 1))/size(ecgData, 1) * tRec, 6000 + ecgData(:, 2), 'r');
xlabel('time (second)');
legend('IMU', 'ECG');

ecg_hi = conv(ecgData(:, 2), [1 -1]);
ecg_std = std(ecg_hi);
ecg_hi_thresh = (ecg_hi > 3*ecg_std);
ecg_hi_thresh_rising = (ecg_hi_thresh - [0; ecg_hi_thresh(1:end-1)]) > 0;
p2p_time = conv(find(ecg_hi_thresh_rising == 1), [1 -1]);
p2p_time = p2p_time(4:end-4);
avg_heart_rate = mean( 60 ./ (p2p_time/ecg_fs) )
%plot((1:size(ecg_hi, 1))/size(ecg_hi, 1) * tRec, ecg_hi_thresh_rising * 12000, 'k');

imufft = abs(fft([imuData(:, 3)]));
imuffth = imufft(2:ceil(end/2));

peakloc = find(imuffth == max(imuffth));
imu_breathing_est = peakloc * imu_fs/2 / size(imuffth, 1) * 60

ecgbrfft = abs(fft(ecgbr));
peakloc = find(ecgbrfft == max(ecgbrfft));
ecg_dr_breathing_est = peakloc(1) * ecg_fs/2 / size(ecgbrfft, 1) * 60