close all; clear all;

imuData = csvread('../data/long_term_lying_down_10mins/cleaned_imu_min3_22bpm.csv');
imu_fs = 100; % imu sampling frequency in Hz

ecgData = csvread('../data/long_term_lying_down_10mins/cleaned_ecg_min3_22bpm.csv');
ecg_fs = 400; % ecg sampling frequency in Hz

plot((1:size(imuData, 1))/imu_fs, imuData(:, 3));
hold on;
plot((1:size(ecgData, 1))/ecg_fs, 6000 + ecgData(:, 2), 'r');

imufft = abs(fft([imuData(:, 3)]));
imuffth = imufft(2:ceil(end/2));

peakloc = find(imuffth == max(imuffth))
imu_breathing_est = peakloc * imu_fs/2 / size(imuffth, 1) * 60

