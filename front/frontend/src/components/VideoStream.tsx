import React, { useEffect, useState } from 'react';
import { io, Socket } from 'socket.io-client';
import axios from 'axios';
import { makeStyles } from '@mui/styles';
import {
    Container,
    Typography,
    Grid,
    Paper,
    Slider
} from '@mui/material';

const useStyles = makeStyles({
    root: {
        flexGrow: 1,
        padding: '2rem'
    },
    frameContainer: {
        marginBottom: '2rem'
    },
    image: {
        width: '100%',
        maxHeight: '300px',
        objectFit: 'cover'
    },
    slider: {
        width: '50%',
        margin: '0 auto',
    }
});

const socket: Socket = io('http://localhost:5000', {
    transports: ['websocket', 'polling']
});

interface Frame {
    frame: string;
    timestamp: number;
}

const VideoStream: React.FC = () => {
    const classes = useStyles();
    const [currentFrame, setCurrentFrame] = useState<string>('');
    const [history, setHistory] = useState<Frame[]>([]);
    const [sliderValue, setSliderValue] = useState<number>(0);
    const [maxSliderValue, setMaxSliderValue] = useState<number>(0);
    const [isStreaming, setIsStreaming] = useState<boolean>(true);

    useEffect(() => {
        fetchHistory();
        startStreaming();

        const interval = setInterval(fetchHistory, 5000);

        return () => {
            clearInterval(interval);
            socket.off('video_frame');
        };
    }, []);

    const fetchHistory = async () => {
        try {
            const response = await axios.get<Frame[]>('http://localhost:5000/history');
            console.log('Fetched history:', response.data);
            setHistory(response.data);
            setMaxSliderValue(response.data.length - 1);
            if (response.data.length > 0 && isStreaming) {
                setCurrentFrame(`data:image/jpeg;base64,${response.data[response.data.length - 1].frame}`);
                setSliderValue(response.data.length - 1); // Set slider to the latest frame
            }
        } catch (error) {
            console.error('Error fetching history:', error);
        }
    };

    const startStreaming = () => {
        socket.on('video_frame', (frame: Frame) => {
            setHistory(prevHistory => {
                const newHistory = [...prevHistory, frame];
                setMaxSliderValue(newHistory.length - 1);
                if (isStreaming) {
                    setSliderValue(newHistory.length - 1); // Move slider to the latest frame
                    setCurrentFrame(`data:image/jpeg;base64,${frame.frame}`);
                }
                return newHistory;
            });
        });
    };

    const handleSliderChange = (event: Event, newValue: number | number[]) => {
        const value = typeof newValue === 'number' ? newValue : 0;
        const selectedTimestamp = history[value].timestamp;
        let closestIndex = 0;
        let minDiff = Math.abs(selectedTimestamp - history[0].timestamp);

        // Find the index of the frame with the closest timestamp to the selected timestamp
        for (let i = 1; i < history.length; i++) {
            const diff = Math.abs(selectedTimestamp - history[i].timestamp);
            if (diff < minDiff) {
                minDiff = diff;
                closestIndex = i;
            }
        }

        setSliderValue(closestIndex);
        setCurrentFrame(`data:image/jpeg;base64,${history[closestIndex].frame}`);
        setIsStreaming(false); // Pause streaming when slider is moved
    };

    const handleResumeStreaming = () => {
        setIsStreaming(true);
        const latestFrame = history[history.length - 1];
        if (latestFrame) {
            setCurrentFrame(`data:image/jpeg;base64,${latestFrame.frame}`);
            setSliderValue(history.length - 1);
        }
    };

    return (
        <Container className={classes.root}>
            <Typography variant="h4" gutterBottom>
                Real-time Video Stream
            </Typography>
            <Grid container spacing={3} className={classes.frameContainer}>
                <Grid item xs={12}>
                    <Paper>
                        {currentFrame ? (
                            <img src={currentFrame} alt="Current frame" className={classes.image} />
                        ) : (
                            <Typography variant="body1">No frame available</Typography>
                        )}
                    </Paper>
                </Grid>
            </Grid>

            <Typography variant="h5" gutterBottom>
                Timeline
            </Typography>
            <Slider
                className={classes.slider}
                value={sliderValue}
                onChange={handleSliderChange}
                onChangeCommitted={handleResumeStreaming}
                min={0}
                max={maxSliderValue}
                step={1}
                valueLabelDisplay="auto"
            />
        </Container>
    );
};

export default VideoStream;
